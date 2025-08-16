from abc import abstractmethod
from dataclasses import dataclass
import json
from typing import override
import boto3
from botocore.exceptions import ClientError
import requests
from tenacity import retry, stop_after_attempt, wait_fixed

from db.model.edinet.document_list_response_type2 import DocumentListResponseType2


@dataclass
class Strategy:
    @abstractmethod
    def execute(self):
        pass


@dataclass
class GetDocumentListFromEdiNetApi(Strategy):
    type: str
    api_key: str
    yyyymmdd: str  # yyyy-mm-dd
    endpoint: str = "https://api.edinet-fsa.go.jp/api/v2/documents.json"

    @override
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
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def execute(self):
        return self.document_list_response.create_result_items()


@dataclass
class DownloadDocumentFromEdiNetApi(Strategy):
    type: str
    api_key: str
    docID: str
    endpoint: str = "https://api.edinet-fsa.go.jp/api/v2/documents/"

    @override
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def execute(self):
        endpoint = self.endpoint + self.docID
        params = {"type": self.type, "Subscription-Key": self.api_key}
        res = requests.get(self.endpoint, params=params)
        res.raise_for_status()


@dataclass
class GetApiKeyFromAws(Strategy):
    secret_name: str
    key_name: str
    region_name: str

    @override
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def execute(self):

        # Create a Secrets Manager client
        session = boto3.Session(profile_name="gb86sub")
        client = session.client(
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
