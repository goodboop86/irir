import asyncio
import json  # Import json for Lambda response


from common.main.lib.model import LocalLambdaContext
from register.main.model.edinet.document_item import DbItem
from register.main.model.edinet.document_list_response_type2 import (
    DocumentListResponseType2,
)
from register.main.model.lambda_event import RegisterLambdaEvent
from register.main.strategy.strategy import (
    CreateAwsSession,
    DownloadDocumentFromEdiNetApi,
    GetApiKeyFromAws,
    GetDocumentListFromEdiNetApi,
    GetItemsFromDocumentListReaponse,
    InsertItemsToDynamoDb,
    UploadToAwsS3,
)


async def lambda_handler(event, context):

    register_event = RegisterLambdaEvent(**event)

    session = CreateAwsSession(event=register_event).execute()

    apikey = GetApiKeyFromAws(
        aws_session=session,
        event=register_event,
    ).execute()

    # Get the list of documents from the EdiNet API
    document_list_response: DocumentListResponseType2 = GetDocumentListFromEdiNetApi(
        type="2", api_key=apikey, yyyymmdd=register_event.YYYYMMDD
    ).execute()

    # Extract items from the document list response
    db_items: list[DbItem] = GetItemsFromDocumentListReaponse(
        document_list_response=document_list_response
    ).execute()

    # Download documents using the extracted items
    db_items: list[DbItem] = await DownloadDocumentFromEdiNetApi(
        api_key=apikey, documentlist=db_items, event=register_event
    ).execute()

    db_items: list[DbItem] = await UploadToAwsS3(
        aws_session=session, db_items=db_items, event=register_event
    ).execute()

    InsertItemsToDynamoDb(
        aws_session=session, items=db_items, event=register_event
    ).execute()


if __name__ == "__main__":

    # event
    config_file_path = "register/main/resources/local_lambda_event.json"
    with open(config_file_path, "r", encoding="utf-8") as f:
        event = json.load(f)

    # context
    local_context = LocalLambdaContext()

    # Run the main function with the retrieved parameters
    asyncio.run(lambda_handler(event=event["INITIAL_EVENT"], context=local_context))
