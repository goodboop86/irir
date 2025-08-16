import json
from pprint import pprint
import boto3

from db.model.edinet.document_list_response_type2 import DocumentListResponseType2
from db.strategy.strategy import (
    GetApiKeyFromAws,
    GetDocumentListFromEdiNetApi,
    GetItemsFromDocumentListReaponse,
)


# with open("app/common/main/resources/document_list_response_type2.json") as f:
#     resp = json.loads(f.read())

# doclist = DocumentListResponseType2(**resp)
# items = doclist.create_result_items()


# session = boto3.Session(profile_name="gb86sub")
# resource = session.resource("dynamodb")

# table_name = "edinet-document_list-api"
# # describe = resource.describe_table(TableName=table_name)
# # pprint(describe)

# table = resource.Table(table_name)

# for item in items:
#     pprint(item)
#     # table.put_item(Item=item)


def run():
    get_apikey = GetApiKeyFromAws(
        secret_name="EdinetApiKey",
        key_name="EDINET_API_KEY",
        region_name="ap-northeast-1",
    )

    get_documentlist = GetDocumentListFromEdiNetApi(
        type="2", api_key=get_apikey.execute(), yyyymmdd="2023-08-28"
    )

    get_items = GetItemsFromDocumentListReaponse(
        document_list_response=get_documentlist.execute()
    )
    pprint(get_items.execute())


if __name__ == "__main__":
    run()
