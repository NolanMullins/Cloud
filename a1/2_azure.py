#!/usr/bin/python3


import time
import string
import json
import csv
import decimal
import os, uuid
#from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.errors as errors
import azure.cosmos.http_constants as http_constants
import azure.cosmos.documents as documents

#https://github.com/Azure/azure-cosmos-python/blob/master/samples/DatabaseManagement/Program.py#L65-L76
#https://pypi.org/project/azure-cosmos/?fbclid=IwAR0_KFgPFAn7jyBNg4mYM7JFqwE-2khDvJzbfpm8ctz47rK7SOR4ldBxX9g

#????
#https://docs.microsoft.com/en-us/python/api/azure-cosmos/azure.cosmos.cosmos_client.cosmosclient?view=azure-python
#https://docs.microsoft.com/en-us/python/api/azure-cosmos/azure.cosmos.cosmosclient?view=azure-python-preview

database_name = 'moviedb'
container_name = 'movies'

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

def getDB(client):
    try:
        try:
            return client.CreateDatabase({'id': database_name})
        except errors.HTTPFailure:
            return client.ReadDatabase("dbs/" + database_name)
    except Exception as e:
        print("Error getting database")
        print(e)

def getContainer(client):
    try:
        container_definition = {'id': container_name,
                                'partitionKey':
                                            {
                                                'paths': ['/year'],
                                                'kind': documents.PartitionKind.Hash
                                            }
                                }
        try:
            return client.CreateContainer("dbs/" + database_name, container_definition, {'offerThroughput': 400})
        except errors.HTTPFailure as e:
            if e.status_code == http_constants.StatusCodes.CONFLICT:
                return client.ReadContainer("dbs/" + database_name + "/colls/" + container_definition['id'])
            else:
                raise e
    except Exception as e:
        print("Error getting container")


def getTable(client):
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

def uploadData(client):
    print("Uploading movie data")
    try:
        t = time.time()
        with open("data/moviedata.json") as json_file:
            movies = json.load(json_file)
            print('loaded movies')
            for movie in movies:
                year = int(movie['year'])
                title = movie['title']
                info = movie['info']
                client.UpsertItem("dbs/" + database_name + "/colls/" + container_name, 
                    {
                        'year': year,
                        'title': title,
                        'info': info,
                    }
                )

        t = time.time() - t
        print("Done uploading data - "+str(t)) 
    except Exception as e:
        print("Error uploading data")
        print(e)

def init(client):
    database = getDB(client)
    container = getContainer(client)
    uploadData(client)
    '''
    if (response['Table']['ItemCount'] == 0):
        uploadData(table)
    else:
        print('Data already in table')
    return table
    '''
    return database

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

def getVal(item, key):
    if (len(key.split('.')) > 1):
        keys = key.split('.')
        tmp = item
        for key in keys:
            tmp = tmp[key]
        return tmp
    else:
        return item[key] 

sortKey = 'year'
def sortHelper(e):
    return getVal(e, sortKey)

def getDisplayAttributes():
    txt = input('Leave blank to continue\nEnter attribute to display:\n')
    attr = []
    while (not len(txt) == 0):
        attr.append(txt)
        txt = input('Leave blank to continue\nEnter attribute to display:\n')
    return attr

def writeCsv(data, attr):
    try:
        outFile = open('query_'+str(int(time.time()))+'.csv', 'w')
        with outFile:
            writer = csv.writer(outFile)
            writer.writerow(attr)
            for item in data:
                row = []
                for key in attr:
                    row.append(getVal(item, key))
                writer.writerow(row)
    except Exception as e:
        print('Error writing file')

def runScan(table, filter):
    global sortKey
    sortKey = input('Sort by: \n')
    if (len(sortKey)==0):
        sortKey = 'year'
    displayAllAttr = input('Display all attributes [y/n] ')=="y"
    attr = ['year', 'title', 'info.rating', 'info.rank', 'info.running_time_secs', 'info.genres', 'info.plot', 'info.directors', 'info.actors']
    if (not displayAllAttr):
        attr = getDisplayAttributes()
    try:
        response = table.scan(
            FilterExpression = filter
        )
        print("Result: ")
        sortedResponse = sorted(response['Items'], key=sortHelper, reverse=True)
        
        #Print out col names
        txt = ""
        for key in attr:
            txt = txt + key + "\t"
        print(txt)

        #Print out query
        for i in sortedResponse:
            txt = ""
            for key in attr:
                txt = txt + str(getVal(i, key)) + "\t"
            print(txt)

        outputCsv = input("Save to csv? [y/n] ") == "y"
        if (outputCsv):
            writeCsv(sortedResponse, attr)

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

        #Look into using this
        #pe = "year, title, info.rating"



if __name__ == "__main__":
    connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    prim_key = "xK1QlnhPCtJuiaIyP6uVAjHtOglOZlHWWZJZ7x5YcCI6QusExAe7szgUyZx8L8hGN0lGCT1Bae58CSbwdb3PSQ=="
    endpoint = "https://cis4010moviedb.documents.azure.com"
    client = cosmos_client.CosmosClient(endpoint,  {'masterKey': prim_key})

    database = init(client)

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

    exit(0)
    running = True
    while (running):
        scan(table)
        running = (input("Run another query? [y/n] ") == "y")

    print("Running")