#!/usr/bin/python3

import time
import string
import json
import decimal
import boto3

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

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

def init(dynamodb, client):
    table = getTable(dynamodb)
    response = client.describe_table(
        TableName=table.name
    )
    if (response['Table']['ItemCount'] == 0):
        uploadData(table)
    else:
        print('Data already in table')
    return table

def initFilter():
        years = input("Filter years, leave blank for all, enter 1 or 2 years\n<year> <year>\n")
        if (len(years)==0):
            return Key('year').between(1900, 9999)
        years = years.split(' ')
        if (len(years) > 1):
            return Key('year').between(int(years[0]), int(years[1]))
        else:
            return Key('year').eq(int(years[0]))

def getFilterAttribute():
    expression = input("Leave blank to continue\n<Attr> <operator> <value>\n")
    if (len(expression) == 0):
        return 0
    expression = expression.split(' ')
    if (len(expression) < 2):
        return -1
    value = int(expression[2]) if expression[2].isdigit() else expression[2]
    if (expression[1] == ">"):
        return Attr(expression[0]).gt(value)
    elif (expression[1] == "<"):
        return Attr(expression[0]).lt(value)
    elif (expression[1] == "="):
        return Attr(expression[0]).eq(value)
    elif (expression[1] == "between"):
        if (len(expression) < 3):
            return -1
        value2 = int(expression[3]) if expression[3].isdigit() else expression[3]
        return Attr(expression[0]).between(value, value2)
    else:
        return -1

sortKey = 'year'
def sortHelper(e):
    if (len(sortKey.split('.')) > 1):
        keys = sortKey.split('.')
        tmp = e
        for key in keys:
            tmp = tmp[key]
        return tmp
    else:
        print('single key')
        return e[sortKey]

def getDisplayAttributes():
    attr = []
    txt = input('Leave blank to continue\nEnter attribute to display:\n')
    while (not len(txt) == 0):
        attr.append(txt)
        txt = input('Leave blank to continue\nEnter attribute to display:\n')
    return attr

def runScan(table, filter):
    global sortKey
    sortKey = input('Sort by: \n')
    if (len(sortKey)==0):
        sortKey = 'year'
    displayAllAttr = input('Display all attributes [y/n]')=="y"
    attr = []
    if (not displayAllAttr):
        attr = getDisplayAttributes()
    try:
        response = table.scan(
            FilterExpression = filter
        )
        print("Result: ")
        sortedResponse = sorted(response['Items'], key=sortHelper, reverse=True)
        for i in sortedResponse:
            if (displayAllAttr):
                print(i['year'], "\t", i['title'], "\t", i['info']['rating'])
            else:
                txt = ""
                for key in attr:
                    txt = txt + i[key] + "\t"
                print(txt)

    except Exception as e:
        print('Error with query, check filter attributes')
        print(e)

def scan(table):
        filter = getFilterAttribute()
        if (filter == -1):
            print('Error with expression')
            return
        if (filter == 0):
            fe = Key('year').between(1900, 9999)
            runScan(table, fe)
        else:
            fe = filter
            building = True
            while (building):
                filter = getFilterAttribute()
                if (filter == -1):
                    print('Error with expression')
                    break
                if (filter == 0):
                    break
                fe = fe & filter
            runScan(table, fe)

        #fe = Key('year').between(1950, 1959)
        #fe = fe & Attr('info.rating').gt(8)

        #LOOK AT USING THIS
        #pe = "year, title, info.rating"



if __name__ == "__main__":
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    client = boto3.client('dynamodb')
    table = init(dynamodb, client)

    print(""""
************
Welcome
Query structure
<term> <operator> <value>
Available operators:
<
>
=
between <value> <value>
************""")

    running = True
    while (running):
        scan(table)
        running = (input("Run another query? [y/n]") == "y")
