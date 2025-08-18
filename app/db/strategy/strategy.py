from abc import abstractmethod
from dataclasses import asdict, dataclass
import json
from pprint import pprint
from typing import override
import boto3
from botocore.exceptions import ClientError
import requests
from tenacity import retry, stop_after_attempt, wait_fixed
from boto3.session import Session

from common.main.lib.utils import Utils
from db.model.edinet.document_item import Results
from db.model.edinet.document_list_response_type2 import DocumentListResponseType2
from db.model.edinet.edinet_enums import DocType


@dataclass
class Strategy:
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
            # For a list of exceptions thrown, see
            # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
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

    @override
    @Utils.trace
    # @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def execute(self):
        resource = self.session.resource("dynamodb")
        table = resource.Table(self.target_table)

        for item in self.items:
            table.put_item(Item=asdict(item))


@dataclass
class DownloadDocumentFromEdiNetApi(Strategy):
    # TODO
    api_key: str
    results: list[Results]
    endpoint: str = "https://api.edinet-fsa.go.jp/api/v2/documents/"

    @override
    @Utils.trace
    def execute(self):
        def to_args(docid, t: DocType, p):
            return {"url": f"{self.endpoint}/{docid}", "filename": f"{docid}__{t.name}.zip", "param": p}

        arglist: list[dict] = []
        args = {
            "Subscription-Key": self.api_key,
        }

        for result in self.results:
            if result.has_xbrl():
                arglist.add(to_args(t=DocType.XBRL, p=args | {"type": "1"}))
            if result.has_pdf():
                arglist.add(to_args(t=DocType.PDF, p=args | {"type": "2"}))
            if result.has_englishdoc():
                arglist.add(to_args(t=DocType.ENGLISH, p=args | {"type": "4"}))
            if result.has_csv():
                arglist.add(to_args(t=DocType.CSV, p=args | {"type": "5"}))

        for args in arglist:
            self.download(**args)

    @Utils.trace
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def download(self, url, filename, param):
        try:
            with requests.get(url, params=param, stream=True) as response:
                # ステータスコードが200（成功）であることを確認
                response.raise_for_status()
                
                # バイナリ書き込みモードでファイルを開く
                with open(filename, 'wb') as f:
                    # チャンクごとにデータを読み込み、ファイルに書き込む
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk: # キープアライブメッセージなどの空のチャンクを除外
                            f.write(chunk)
            
            print(f"ファイルのダウンロードが完了しました: {filename}")
        
        except requests.RequestException as e:
            print(f"ダウンロード中にエラーが発生しました: {e}")
        except IOError as e:
            print(f"ファイル書き込み中にエラーが発生しました: {e}")
