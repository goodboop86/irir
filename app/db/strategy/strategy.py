from abc import abstractmethod
from dataclasses import dataclass
import json
from pprint import pprint
from typing import override
import boto3
from botocore.exceptions import ClientError
import requests
from tenacity import retry, stop_after_attempt, wait_fixed
from boto3.session import Session

from common.main.lib.utils import Utils
from db.model.edinet.document_list_response_type2 import DocumentListResponseType2


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
    def execute(self):
        # import pdb;pdb.set_trace()
        return self.document_list_response.create_result_items()


@dataclass
class InsertItemsToDynamoDb(Strategy):
    session: Session
    items: list[dict]
    target_table: str

    @override
    @Utils.trace
    # @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def execute(self):
        resource = self.session.resource("dynamodb")
        table = resource.Table(self.target_table)

        for item in self.items:
            table.put_item(Item=item)


@dataclass
class DownloadDocumentFromEdiNetApi(Strategy):
    # TODO
    type: str
    api_key: str
    docID: str
    endpoint: str = "https://api.edinet-fsa.go.jp/api/v2/documents/"

    @override
    @Utils.trace
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def execute(self):
        endpoint = self.endpoint + self.docID
        params = {"type": self.type, "Subscription-Key": self.api_key}
        res = requests.get(self.endpoint, params=params)
        res.raise_for_status()
