from abc import abstractmethod
from dataclasses import asdict, dataclass, field
import json
import logging
import os
from pprint import pprint
from typing import List, Optional, override
import boto3
from botocore.exceptions import ClientError
import asyncio
import aiohttp
import aiofiles
import requests
from tenacity import retry, stop_after_attempt, wait_fixed
from boto3.session import Session

from common.main.lib.utils import Utils
from db.model.edinet.document_item import DbInfo, DbItem, FileInfo, Results
from db.model.edinet.document_list_response_type2 import DocumentListResponseType2
from db.model.edinet.edinet_enums import DocType
from boto3.dynamodb.conditions import Key


@dataclass
class Strategy:
    logger = logging.getLogger(__name__)
    @abstractmethod
    def execute(self):
        pass


@dataclass
class CreateAwsSession(Strategy):
    profile_name: str

    @override
    @Utils.trace
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def execute(self):
        return boto3.Session(profile_name=self.profile_name)


@dataclass
class GetApiKeyFromAws(Strategy):
    session: Session
    secret_name: str
    key_name: str
    region_name: str

    @override
    @Utils.trace
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def execute(self):
        # Create a Secrets Manager client
        client = self.session.client(
            service_name="secretsmanager", region_name=self.region_name
        )
        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=self.secret_name
            )
        except ClientError as e:
            raise e
        secret = get_secret_value_response["SecretString"]
        return json.loads(secret)[self.key_name]


@dataclass
class GetDocumentListFromEdiNetApi(Strategy):
    type: str
    api_key: str
    yyyymmdd: str  # yyyy-mm-dd
    endpoint: str = "https://api.edinet-fsa.go.jp/api/v2/documents.json"

    @override
    @Utils.trace
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
    @Utils.trace
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def execute(self) -> list[Results]:
        return self.document_list_response.create_valid_result_items()


@dataclass
class InsertItemsToDynamoDb(Strategy):
    session: Session
    items: list[Results]
    target_table: str

    def __post_init__(self):
        resource = self.session.resource("dynamodb")
        self.table = resource.Table(self.target_table)

    @override
    @Utils.trace # This is a synchronous method
    # @retry(stop=stop_after_attempt(3), wait=wait_fixed(1)) # Retry might need async version for async methods
    def execute(self):
        resource = self.session.resource("dynamodb")
        table = resource.Table(self.target_table)
        for item in self.items:
            if not self.doc_id_exists(gsi_name="docID-index", target=item.docID):
                self.insert(table, asdict(item))
            else:
                self.logger.info(f"[SKIP]{item.docID} is already exists.")
    
    def doc_id_exists(self, gsi_name, target):
        """
        指定されたdocIDがGSIに存在するかを確認する。
        """
        try:
            response = self.table.query(
                IndexName=gsi_name,
                KeyConditionExpression=Key('docID').eq(target),
                ProjectionExpression='docID'
            )
            return len(response['Items']) > 0
        except ClientError as e:
            print(f"クエリ中にエラーが発生しました: {e.response['Error']['Message']}")
            return False

    @Utils.trace # This is a synchronous method
    def insert(self, table, item):
        table.put_item(Item=item)


@dataclass
class DownloadDocumentFromEdiNetApi(Strategy):
    api_key: str
    results: list[Results]
    work_dir: str
    endpoint: str = "https://api.edinet-fsa.go.jp/api/v2/documents/"

    @override
    @Utils.trace
    async def execute(self):

        async with aiohttp.ClientSession() as session:
            tasks = [self.download(session, result) for result in self.results]
            db_items: list[DbItem] = await asyncio.gather(*tasks)
            return db_items


    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def download(self, session: aiohttp.ClientSession, results: Results):

        db_item = DbItem(**asdict(results))

        
        url = f"{self.endpoint}/{db_item.docID}"

        param = {
            "Subscription-Key": self.api_key,
        }

        save_dir = f"{self.work_dir}/{db_item.edinetCode}/{db_item.docID}"
        os.makedirs(save_dir, exist_ok=True)

        if db_item.has_xbrl():
            filepath: str = f"{save_dir}/{DocType.XBRL.name}.zip"
            is_success = await self.savefile(session=session, url=url, param=param | {"type": "1"},filepath=filepath)
            if is_success:
                db_item.xbrl_info = FileInfo(filepath=filepath)
        
        if db_item.has_pdf():
            filepath: str = f"{save_dir}/{DocType.PDF.name}.zip"
            is_success = await self.savefile(session=session, url=url, param=param | {"type": "2"},filepath=filepath)
            if is_success:
                db_item.pdf_info = FileInfo(filepath=filepath)

        if db_item.has_attachdoc():
            filepath: str = f"{save_dir}/{DocType.ATTACH.name}.zip"
            is_success = await self.savefile(session=session, url=url, param=param | {"type": "4"},filepath=filepath)
            if is_success:
                db_item.english_info = FileInfo(filepath=filepath)
        
        if db_item.has_englishdoc():
            filepath: str = f"{save_dir}/{DocType.ENGLISH.name}.zip"
            is_success = await self.savefile(session=session, url=url, param=param | {"type": "4"},filepath=filepath)
            if is_success:
                db_item.english_info = FileInfo(filepath=filepath)
        
        if db_item.has_csv():
            filepath: str = f"{save_dir}/{DocType.CSV.name}.zip"
            is_success = await self.savefile(session=session, url=url, param=param | {"type": "5"},filepath=filepath)
            if is_success:
                db_item.csv_info = FileInfo(filepath=filepath)

        return db_item



    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def savefile(self, session: aiohttp.ClientSession, url: str, param: dict, filepath: str) -> bool:

        try:
            async with session.get(url, params=param) as response:
                response.raise_for_status()
                
                async with aiofiles.open(f"{filepath}", 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
            
            self.logger.info(f"[DONE] download [{filepath}]")
        
            return True

        except aiohttp.ClientError as e:
            self.logger.error(f"error while downloading [{filepath}]: {e}")
            return False
        except IOError as e:
            self.logger.error(f"error while file writing [{filepath}]: {e}")
            return False

    
    # @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    # async def download_(self, session: aiohttp.ClientSession, url: str, doctype: DocType, param: dict, save_dir: str, results: Results):

    #     os.makedirs(save_dir, exist_ok=True)

    #     save_path = f"{save_dir}/{doctype}" # "# {docid}__{t.doctype}.zip"

    #     try:
    #         async with session.get(url, params=param) as response:
    #             response.raise_for_status()
                
    #             async with aiofiles.open(f"{save_path}", 'wb') as f:
    #                 async for chunk in response.content.iter_chunked(8192):
    #                     await f.write(chunk)
            
    #         self.logger.info(f"[DONE]download: {doctype}")
        
    #         return save_path

    #     except aiohttp.ClientError as e:
    #         self.logger.error(f"error while downloading [{doctype}]: {e}")
    #     except IOError as e:
    #         self.logger.error(f"error while file writing [{doctype}]: {e}")
