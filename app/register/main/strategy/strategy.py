from abc import abstractmethod
from dataclasses import asdict, dataclass
import json
import logging
import os
from typing import override
import boto3
from botocore.exceptions import ClientError
import asyncio
import aiohttp
import aiofiles
import requests
from tenacity import retry, stop_after_attempt, wait_fixed
from boto3.session import Session

from common.main.lib.utils import Utils
from register.main.model.edinet.document_item import DbItem, FileInfo, Results
from register.main.model.edinet.document_list_response_type2 import (
    DocumentListResponseType2,
)
from register.main.model.edinet.edinet_enums import DocType
from register.main.model.lambda_event import RegisterLambdaEvent


@dataclass
class Strategy:
    logger = logging.getLogger(__name__)

    @abstractmethod
    def execute(self):
        pass


@dataclass
class AwsLambdaStrategy(Strategy):
    event: RegisterLambdaEvent

    @abstractmethod
    def execute(self):
        pass


@dataclass
class CreateAwsSession(AwsLambdaStrategy):

    @override
    @Utils.log_exception
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def execute(self):
        if self.event.ENV == "lambda":
            return boto3.Session()

        return boto3.Session(profile_name=self.event.AWS_PROFILE)


@dataclass
class GetApiKeyFromAws(AwsLambdaStrategy):
    aws_session: Session

    @override
    @Utils.exception
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def execute(self):
        region_name = self.event.AWS_REGION_NAME
        secret_name = self.event.AWS_SECRET_MANAGER__SECRET_NAME
        key_name = self.event.AWS_SECRET_MANAGER__SECRET_KEY_NAME

        client = self.aws_session.client(
            service_name="secretsmanager", region_name=region_name
        )
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = get_secret_value_response["SecretString"]

        return json.loads(secret)[key_name]


@dataclass
class GetDocumentListFromEdiNetApi(Strategy):
    type: str
    api_key: str
    yyyymmdd: str  # yyyy-mm-dd
    endpoint: str = "https://api.edinet-fsa.go.jp/api/v2/documents.json"

    @override
    @Utils.log_exception
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def execute(self):
        params = {
            "date": self.yyyymmdd,
            "type": self.type,
            "Subscription-Key": self.api_key,
        }
        res = requests.get(self.endpoint, params=params)
        res.raise_for_status()
        return DocumentListResponseType2(**res.json())


@dataclass
class GetItemsFromDocumentListReaponse(Strategy):
    document_list_response: DocumentListResponseType2

    @override
    @Utils.log_exception
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def execute(self) -> list[Results]:
        self.document_list_response.filter_valid_result_items()
        return self.document_list_response


@dataclass
class DownloadDocumentFromEdiNetApi(AwsLambdaStrategy):
    api_key: str
    documentlist: DocumentListResponseType2
    endpoint: str = "https://api.edinet-fsa.go.jp/api/v2/documents/"

    @override
    @Utils.log_exception
    async def execute(self):
        async with aiohttp.ClientSession() as aiosession:
            tasks = [
                self.download(aiosession, result)
                for result in self.documentlist.results[:10]
            ]
            db_items: list[DbItem] = await asyncio.gather(*tasks)
            return db_items

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def download(self, session: aiohttp.ClientSession, results: Results):

        db_item = DbItem(**asdict(results))

        url = f"{self.endpoint}/{db_item.docID}"

        param = {
            "Subscription-Key": self.api_key,
        }

        save_dir = f"{self.event.WORK_DIR}/{db_item.edinetCode}/{db_item.submitDateTime}/{db_item.docID}"
        os.makedirs(save_dir, exist_ok=True)

        if db_item.has_xbrl():
            filepath: str = f"{save_dir}/{DocType.XBRL.name}.zip"
            is_success = await self.save(
                session=session, url=url, param=param | {"type": "1"}, filepath=filepath
            )
            if is_success:
                db_item.xbrl_info = FileInfo(filepath=filepath)

        if db_item.has_pdf():
            filepath: str = f"{save_dir}/{DocType.PDF.name}.zip"
            is_success = await self.save(
                session=session, url=url, param=param | {"type": "2"}, filepath=filepath
            )
            if is_success:
                db_item.pdf_info = FileInfo(filepath=filepath)

        if db_item.has_attachdoc():
            filepath: str = f"{save_dir}/{DocType.ATTACH.name}.zip"
            is_success = await self.save(
                session=session, url=url, param=param | {"type": "4"}, filepath=filepath
            )
            if is_success:
                db_item.english_info = FileInfo(filepath=filepath)

        if db_item.has_englishdoc():
            filepath: str = f"{save_dir}/{DocType.ENGLISH.name}.zip"
            is_success = await self.save(
                session=session, url=url, param=param | {"type": "4"}, filepath=filepath
            )
            if is_success:
                db_item.english_info = FileInfo(filepath=filepath)

        if db_item.has_csv():
            filepath: str = f"{save_dir}/{DocType.CSV.name}.zip"
            is_success = await self.save(
                session=session, url=url, param=param | {"type": "5"}, filepath=filepath
            )
            if is_success:
                db_item.csv_info = FileInfo(filepath=filepath)

        return db_item

    @Utils.exception
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def save(
        self, session: aiohttp.ClientSession, url: str, param: dict, filepath: str
    ) -> bool:
        async with session.get(url, params=param) as response:
            response.raise_for_status()
            async with aiofiles.open(f"{filepath}", "wb") as f:
                async for chunk in response.content.iter_chunked(8192):
                    await f.write(chunk)

        self.logger.info(f"[DONE] download [{filepath}]")

        return True


@dataclass
class UploadToAwsS3(AwsLambdaStrategy):
    aws_session: Session
    db_items: list[DbItem]
    bucket = None

    def __post_init__(self):
        resource = self.aws_session.resource("s3")
        self.bucket = resource.Bucket(self.event.AWS_S3__BUCKET_NAME)

    @override
    @Utils.log_exception
    async def execute(self) -> list[DbItem]:
        tasks = [self.upload(item) for item in self.db_items]
        return await asyncio.gather(*tasks)

    @override
    @Utils.exception
    async def upload(self, item: DbItem):

        for info in item.get_infolist():
            if info.filepath:
                await self.save(info=info)
        return item

    @override
    @Utils.exception
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def save(self, info: FileInfo):
        async with aiofiles.open(info.filepath, "rb") as f:
            file_content = await f.read()
        await asyncio.to_thread(
            self.bucket.put_object, Key=info.filepath, Body=file_content
        )
        self.logger.info(f"[DONE] upload [{info.filepath}]")
        info.cloudpath = f"s3://{self.bucket.name}.s3.{self.event.AWS_REGION_NAME}.amazonaws.com/{info.filepath}"


@dataclass
class InsertItemsToDynamoDb(AwsLambdaStrategy):
    aws_session: Session
    items: list[DbItem]

    def __post_init__(self):
        resource = self.aws_session.resource("dynamodb")
        self.table = resource.Table(self.event.AWS_DYNAMODB__TARGET_TABLE)

    @override
    @Utils.log_exception
    def execute(self):
        for item in self.items:
            if not self.doc_id_exists(
                doc_id=item.docID, submit_date_time=item.submitDateTime
            ):
                self.insert(asdict(item))
            else:
                self.logger.info(f"[SKIP]{item.docID} is already exists.")

    @Utils.exception
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def doc_id_exists(self, doc_id, submit_date_time):
        """
        指定されたdocIDがGSIに存在するかを確認する。
        """
        try:
            response = self.table.get_item(
                Key={"docID": doc_id, "submitDateTime": submit_date_time},
                ProjectionExpression=doc_id,
            )
            return "Item" in response
        except ClientError as e:
            print(f"クエリ中にエラーが発生しました: {e.response['Error']['Message']}")
            return False

    @Utils.exception
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def insert(self, item):
        self.table.put_item(Item=item)
