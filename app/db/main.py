from dataclasses import asdict
import json
from pprint import pprint
import boto3

from db.model.edinet.document_item import Results
from db.model.edinet.document_list_response_type2 import DocumentListResponseType2
from db.strategy.strategy import (
    CreateAwsSession,
    DownloadDocumentFromEdiNetApi,
    GetApiKeyFromAws,
    GetDocumentListFromEdiNetApi,
    GetItemsFromDocumentListReaponse,
    InsertItemsToDynamoDb,
)


# with open("app/common/main/resources/document_list_response_type2.json") as f:
#     resp = json.loads(f.read())


def run():

    profile = "gb86sub"
    secret_name="EdinetApiKey"
    key_name="EDINET_API_KEY"
    region_name="ap-northeast-1"
    yyyymmdd="2023-08-28"
    target_table="edinet-document_list-api"
    

    session = CreateAwsSession(profile_name=profile).execute()

    apikey = GetApiKeyFromAws(
        session=session,
        secret_name=secret_name,
        key_name=key_name,
        region_name=region_name,
    ).execute()

    documentlist = GetDocumentListFromEdiNetApi(
        type="2", api_key=apikey, yyyymmdd=yyyymmdd
    ).execute()

    items: list[Results] = GetItemsFromDocumentListReaponse(
        document_list_response=documentlist
    ).execute()

    DownloadDocumentFromEdiNetApi(api_key=apikey, results=items).execute()


    InsertItemsToDynamoDb(
        session=session, items=items, target_table=target_table
    ).execute()



    # pprint(items)


if __name__ == "__main__":
    run()
