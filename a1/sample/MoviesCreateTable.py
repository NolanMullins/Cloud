#!/usr/bin/env python
# coding: utf-8
#
# Example code to create a NoSQL DynamoDB table
#

from __future__ import print_function # Python 2/3 compatibility
import boto3

# Establish a connection to the AWS resource dynamodb

dynamodb = boto3.resource('dynamodb', region_name='ca-central-1')

# Create a new table called MovieInfo

table = dynamodb.create_table(
    TableName='Movies',
    KeySchema=[
        {
            'AttributeName': 'year',
            'KeyType': 'HASH'  #Partition key
        },
        {
            'AttributeName': 'title',
            'KeyType': 'RANGE'  #Sort key
        }
    ],
    AttributeDefinitions=[
        {
            'AttributeName': 'year',
            'AttributeType': 'N'
        },
        {
            'AttributeName': 'title',
            'AttributeType': 'S'
        },

    ],
    ProvisionedThroughput={
        'ReadCapacityUnits': 10,
        'WriteCapacityUnits': 10
    }
)

print("Table status:", table.table_status, table.table_name)

