import json
from pprint import pprint
import boto3
import requests

from db.model.edinet.document_list_response_type2 import DocumentListResponseType2



with open("app/common/main/resources/document_list_response_type2.json") as f:
    resp = json.loads(f.read())

doclist = DocumentListResponseType2(**resp)
items = doclist.create_result_items()

session = boto3.Session(profile_name='gb86sub')
resource = session.resource('dynamodb')

table_name = 'edinet-document_list-api'
# describe = resource.describe_table(TableName=table_name)
# pprint(describe)

table = resource.Table(table_name)

for item in items:
    pprint(item)
    # table.put_item(Item=item)



# import pdb; pdb.set_trace()