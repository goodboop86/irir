import json
import boto3
import requests

from db.model.edinet.document_list_response_type2 import DocumentListResponseType2



resp = requests.get("https://api.edinet-fsa.go.jp/api/v2/documents.json?date=2023-08-28&type=2&Subscription-Key=b96412004635453b95a2490d0cfb2e73")

with open("app/common/main/resources/document_list_response_type2.json") as f:
    resp = json.loads(f.read())

metadata = DocumentListResponseType2(**resp)

print(metadata)

session = boto3.Session(profile_name='gb86sub')
client = session.client('dynamodb')
res = client.describe_table(TableName='edinet-document_list-api')

print(res)