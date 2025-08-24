import asyncio
import os

from dotenv import load_dotenv

from db.main.model.edinet.document_item import DbItem
from db.main.model.edinet.document_list_response_type2 import DocumentListResponseType2
from db.main.strategy.strategy import (
    CreateAwsSession,
    DownloadDocumentFromEdiNetApi,
    GetApiKeyFromAws,
    GetDocumentListFromEdiNetApi,
    GetItemsFromDocumentListReaponse,
    InsertItemsToDynamoDb,
    UploadToAwsS3,
)


async def run():

    load_dotenv()

    aws_profile = os.getenv("AWS_PROFILE")
    aws_secret_manager__secret_name = os.getenv("AWS_SECRET_MANAGER__SECRET_NAME")
    aws_secret_manager__secret_key_name = os.getenv(
        "AWS_SECRET_MANAGER__SECRET_KEY_NAME"
    )
    aws_s3__bucket_name = os.getenv("AWS_S3__BUCKET_NAME")
    aws_region_name = os.getenv("AWS_REGION_NAME")
    aws_dynamodb__target_table = os.getenv("AWS_DYNAMODB__TARGET_TABLE")
    yyyymmdd = os.getenv("YYYYMMDD")
    work_dir = os.getenv("WORK_DIR")

    session = CreateAwsSession(profile_name=aws_profile).execute()

    apikey = GetApiKeyFromAws(
        aws_session=session,
        secret_name=aws_secret_manager__secret_name,
        key_name=aws_secret_manager__secret_key_name,
        region_name=aws_region_name,
    ).execute()

    documentlist: DocumentListResponseType2 = GetDocumentListFromEdiNetApi(
        type="2", api_key=apikey, yyyymmdd=yyyymmdd
    ).execute()

    documentlist: DocumentListResponseType2 = GetItemsFromDocumentListReaponse(
        document_list_response=documentlist
    ).execute()

    db_items: list[DbItem] = await DownloadDocumentFromEdiNetApi(
        api_key=apikey, documentlist=documentlist, work_dir=work_dir
    ).execute()

    db_items: list[DbItem] = await UploadToAwsS3(
        aws_session=session,
        db_items=db_items,
        region_name=aws_region_name,
        s3_bucket_name=aws_s3__bucket_name,
    ).execute()

    InsertItemsToDynamoDb(
        aws_session=session, items=db_items, target_table=aws_dynamodb__target_table
    ).execute()


if __name__ == "__main__":
    asyncio.run(run())
