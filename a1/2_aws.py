#!/usr/bin/python3

import time
import string
import json
import decimal
import boto3
from botocore.exceptions import ClientError

def getTable(dynamodb):
    print("Retrieving table")
    t = time.time()
    try:
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
        t = time.time() - t
        print("Done creating table - "+str(t))
        return table
    except ClientError as e:
        #Table probably exists already
        try:
            table = dynamodb.Table('Movies')
            t = time.time() - t
            print("Done retrieving table - "+str(t))
            return table
        except ClientError as e:
            print("Error, could not find or create movie db")
            exit(0)

def uploadData(table):
    print("Uploading movie data")
    try:
        t = time.time()
        with open("data/moviedata.json") as json_file:
            movies = json.load(json_file, parse_float = decimal.Decimal)
            for movie in movies:
                year = int(movie['year'])
                title = movie['title']
                info = movie['info']

                table.put_item(
                Item={
                    'year': year,
                    'title': title,
                    'info': info,
                    }
                )
        t = time.time() - t
        print("Done uploading data - "+str(t)) 
    except ClientError as e:
        print("Error uploading data")

def init():

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    client = boto3.client('dynamodb')

    table = getTable(dynamodb)
    response = client.describe_table(
        TableName=table.name
    )
    
    if (response['Table']['ItemCount'] == 0):
        uploadData(table)
    else:
        print('Data already in table')


if __name__ == "__main__":
    init()
