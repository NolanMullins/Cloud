#!/usr/bin/env python
# coding: utf-8

from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
import decimal
from boto3.dynamodb.conditions import Key, Attr

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

# Use Query to find all movies in 1950

response = table.query(
    KeyConditionExpression=Key('year').eq(1950)
)

print("1950 Movies")

for i in response['Items']:
    print ( i['year'], "-", i['title'])

# Use Scan to find all movies with a rating greater than 9

print("9+ Movies")

response = table.scan(
    FilterExpression=Attr('info.rating').gt(9)
)

for i in response['Items']:
    print ( i['year'], "-", i['title'])
    
