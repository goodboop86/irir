import asyncio
import os
import json # Import json for Lambda response

from dotenv import load_dotenv # This might not be needed in Lambda environment

from register.main.model.edinet.document_item import DbItem
from register.main.model.edinet.document_list_response_type2 import DocumentListResponseType2
from register.main.strategy.strategy import (
    CreateAwsSession,
    DownloadDocumentFromEdiNetApi,
    GetApiKeyFromAws,
    GetDocumentListFromEdiNetApi,
    GetItemsFromDocumentListReaponse,
    InsertItemsToDynamoDb,
    UploadToAwsS3,
)


async def run(
    aws_profile: str,
    aws_secret_manager__secret_name: str,
    aws_secret_manager__secret_key_name: str,
    aws_s3__bucket_name: str,
    aws_region_name: str,
    aws_dynamodb__target_table: str,
    yyyymmdd: str,
    work_dir: str,
):
    # Validate all required parameters
    if not all([
        aws_profile,
        aws_secret_manager__secret_name,
        aws_secret_manager__secret_key_name,
        aws_s3__bucket_name,
        aws_region_name,
        aws_dynamodb__target_table,
        yyyymmdd,
        work_dir,
    ]):
        raise ValueError("One or more required parameters are missing or empty.")

    # load_dotenv() is removed as it's not needed when passing args

    session = CreateAwsSession(profile_name=aws_profile).execute()

    apikey = GetApiKeyFromAws(
        aws_session=session,
        secret_name=aws_secret_manager__secret_name,
        key_name=aws_secret_manager__secret_key_name,
        region_name=aws_region_name,
    ).execute()

    # Get the list of documents from the EdiNet API
    document_list_response: DocumentListResponseType2 = GetDocumentListFromEdiNetApi(
        type="2", api_key=apikey, yyyymmdd=yyyymmdd
    ).execute()

    # Extract items from the document list response
    db_items: list[DbItem] = GetItemsFromDocumentListReaponse(
        document_list_response=document_list_response
    ).execute()

    # Download documents using the extracted items
    db_items: list[DbItem] = await DownloadDocumentFromEdiNetApi(
        api_key=apikey, documentlist=db_items, work_dir=work_dir # Changed documentlist to db_items
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
    # Load environment variables from .env file for local execution
    load_dotenv()

    # Read environment variables for local execution
    aws_profile = os.getenv("AWS_PROFILE")
    aws_secret_manager__secret_name = os.getenv("AWS_SECRET_MANAGER__SECRET_NAME")
    aws_secret_manager__secret_key_name = os.getenv("AWS_SECRET_MANAGER__SECRET_KEY_NAME")
    aws_s3__bucket_name = os.getenv("AWS_S3__BUCKET_NAME")
    aws_region_name = os.getenv("AWS_REGION_NAME")
    aws_dynamodb__target_table = os.getenv("AWS_DYNAMODB__TARGET_TABLE")
    yyyymmdd = os.getenv("YYYYMMDD")
    work_dir = os.getenv("WORK_DIR")

    # Validate parameters and raise ValueError if any are missing for __main__ execution
    if not all([
        aws_profile,
        aws_secret_manager__secret_name,
        aws_secret_manager__secret_key_name,
        aws_s3__bucket_name,
        aws_region_name,
        aws_dynamodb__target_table,
        yyyymmdd,
        work_dir,
    ]):
        raise ValueError("One or more required parameters are missing or empty for __main__ execution.")

    # Run the main function with the retrieved parameters
    asyncio.run(run(
        aws_profile=aws_profile,
        aws_secret_manager__secret_name=aws_secret_manager__secret_name,
        aws_secret_manager__secret_key_name=aws_secret_manager__secret_key_name,
        aws_s3__bucket_name=aws_s3__bucket_name,
        aws_region_name=aws_region_name,
        aws_dynamodb__target_table=aws_dynamodb__target_table,
        yyyymmdd=yyyymmdd,
        work_dir=work_dir,
    ))


# AWS Lambda Handler
def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    It retrieves parameters from the event, validates them, and then calls the run function.
    """
    # Extract parameters from the event, raising ValueError if any are missing
    try:
        aws_profile = event["AWS_PROFILE"]
        aws_secret_manager__secret_name = event["AWS_SECRET_MANAGER__SECRET_NAME"]
        aws_secret_manager__secret_key_name = event["AWS_SECRET_MANAGER__SECRET_KEY_NAME"]
        aws_s3__bucket_name = event["AWS_S3__BUCKET_NAME"]
        aws_region_name = event["AWS_REGION_NAME"]
        aws_dynamodb__target_table = event["AWS_DYNAMODB__TARGET_TABLE"]
        yyyymmdd = event["YYYYMMDD"]
        work_dir = event["WORK_DIR"]
    except KeyError as e:
        raise ValueError(f"Missing required parameter in event payload: {e}") from e

    try:
        # Run the main function with the parameters from the event
        asyncio.run(run(
            aws_profile=aws_profile,
            aws_secret_manager__secret_name=aws_secret_manager__secret_name,
            aws_secret_manager__secret_key_name=aws_secret_manager__secret_key_name,
            aws_s3__bucket_name=aws_s3__bucket_name,
            aws_region_name=aws_region_name,
            aws_dynamodb__target_table=aws_dynamodb__target_table,
            yyyymmdd=yyyymmdd,
            work_dir=work_dir,
        ))
        return {
            'statusCode': 200,
            'body': json.dumps('AWS Lambda execution completed successfully!')
        }
    except Exception as e:
        # Log the error and return an error response
        print(f"Error during AWS Lambda execution: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error during AWS Lambda execution: {str(e)}')
        }
