#!/usr/bin/env python
# coding: utf-8

from __future__ import print_function # Python 2/3 compatibility
import boto3
from botocore.exceptions import ClientError
import json
import decimal

# Helper class to convert a DynamoDB item to JSON.

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

dynamodb = boto3.resource('dynamodb', region_name='ca-central-1')

table = dynamodb.Table('Movies')

title = "My Big New Movie"
year = 2020

print("Attempting a delete...")

response = table.delete_item(
    Key={
        'year': year,
        'title': title
    }
)
print("DeleteItem succeeded:")
print(json.dumps(response, indent=4, cls=DecimalEncoder))

