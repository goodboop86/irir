from abc import abstractmethod
from dataclasses import asdict, dataclass, field
import json
import logging
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
from db.model.edinet.document_item import Results
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
    endpoint: str = "https://api.edinet-fsa.go.jp/api/v2/documents/"

    @override
    @Utils.trace
    async def execute(self):
        async def to_args(docid, t: DocType, p):
            return {"url": f"{self.endpoint}/{docid}", "filename": f"{docid}__{t.name}.zip", "param": p}

        arglist: list[dict] = []
        args = {
            "Subscription-Key": self.api_key,
        }

        for result in self.results:
            if result.has_xbrl():
                arglist.append(await to_args(docid=result.docID, t=DocType.XBRL, p=args | {"type": "1"}))
            if result.has_pdf():
                arglist.append(await to_args(docid=result.docID, t=DocType.PDF, p=args | {"type": "2"}))
            if result.has_englishdoc():
                arglist.append(await to_args(docid=result.docID, t=DocType.ENGLISH, p=args | {"type": "4"}))
            if result.has_csv():
                arglist.append(await to_args(docid=result.docID, t=DocType.CSV, p=args | {"type": "5"}))

        async with aiohttp.ClientSession() as session:
            tasks = [self.download(session, **args) for args in arglist[:10]]
            await asyncio.gather(*tasks)

    async def download(self, session: aiohttp.ClientSession, url: str, filename: str, param: dict):
        try:
            async with session.get(url, params=param) as response:
                response.raise_for_status()
                
                async with aiofiles.open(filename, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
            
            self.logger.info(f"[DONE]download: {filename}")
        
        except aiohttp.ClientError as e:
            self.logger.error(f"error while downloading: {e}")
        except IOError as e:
            self.logger.error(f"error while file writing: {e}")
