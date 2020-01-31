#!/usr/bin/python3

#Not done, WIP

import os
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

def uploadData(client):
    print("Uploading movie data")
    try:
        t = time.time()
        with open("data/moviedata.json") as json_file:
            movies = json.load(json_file)
            for movie in movies:
                year = int(movie['year'])
                title = movie['title']
                info = movie['info']
                client.UpsertItem("dbs/" + database_name + "/colls/" + container_name, {
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

    items = client.QueryItems("dbs/" + database_name + "/colls/" + container_name,
                            'SELECT TOP 1 * FROM ' + container_name + ' r',
                            {'enableCrossPartitionQuery': True})

    flag = False
    for item in items:
        flag = True

    if (not flag):
        uploadData(client)
    else:
        print('Data already in table')

def getFilterAttribute():
    expression = input("Leave blank to continue\n<Attr> <operator> <value>\n")
    if (len(expression) == 0):
        return 0
    expression = expression.split(' ')
    if (len(expression) < 2):
        return -1
    op = expression[1]
    if (op == "between"):
        if (len(expression) < 3):
            return -1
        return '(r.'+expression[0] + ' BETWEEN ' + expression[2] + ' AND ' + expression[3]+')'
    elif(op == ">" or op == "<" or op == "="):
        return '(r.'+expression[0] + op + expression[2]+')'
    else:
        return -1

def getVal(item, key):
    try:
        if (len(key.split('.')) > 1):
            keys = key.split('.')
            tmp = item
            for key in keys:
                tmp = tmp[key]
            return tmp
        else:
            return item[key] 
    except Exception:
        return "N/A"

sortKey = 'year'
def sortHelper(e):
    return getVal(e, sortKey)

def getDisplayAttributes():
    txt = input('Leave blank to continue\nEnter attribute to display:\n')
    attr = []
    while (not len(txt) == 0):
        attr.append(txt)
        txt = input('Next:\n')
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

def runQuery(client, expression):
    print(expression)
    global sortKey
    sortKey = input('Sort by: \n')
    displayAllAttr = input('Display all attributes [y/n] ')=="y"
    attr = ['year', 'title', 'info.rating', 'info.rank', 'info.running_time_secs', 'info.genres', 'info.plot', 'info.directors', 'info.actors']
    if (not displayAllAttr):
        attr = getDisplayAttributes()
    try:
        t = time.time()
        filter = expression
        if (len(filter) > 0):
            filter = 'WHERE '+filter
        items = client.QueryItems("dbs/" + database_name + "/colls/" + container_name,
                              'SELECT * FROM ' + container_name + ' r '+filter,
                              {'enableCrossPartitionQuery': True})
        print("Result: ")
        t = time.time() - t
        print("Time taken - "+str(t)) 
        try:
            if (len(sortKey)>0):
                items = sorted(items, key=sortHelper, reverse=True)
        except Exception:
            print("Error sorting items, some items did not contain the sort key")
        
        #Print out col names
        txt = ""
        for key in attr:
            txt = txt + key + "\t"
        print(txt)

        #Print out query
        for i in items:
            txt = ""
            for key in attr:
                txt = txt + str(getVal(i, key)) + "\t"
            print(txt)

        outputCsv = input("Save to csv? [y/n] ") == "y"
        if (outputCsv):
            writeCsv(items, attr)

    except Exception as e:
        print('Error with query, check filter attributes')
        print(e)

def query(client):
        expression = getFilterAttribute()
        if (expression == -1):
            print('Error with expression')
            return
        if (expression == 0):
            runQuery(client, '')
        else:
            building = True
            while (building):
                filter = getFilterAttribute()
                if (filter == -1):
                    print('Error with expression')
                    break
                if (filter == 0):
                    break
                expression = expression + ' AND ' + filter
            runQuery(client, expression)

if __name__ == "__main__":
    url = os.environ['ACCOUNT_URI']
    key = os.environ['ACCOUNT_KEY']
    client = cosmos_client.CosmosClient(url, {'masterKey': key})

    #Currently fails to initialize
    init(client)

    print("""
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
        query(client)
        running = (input("Run another query? [y/n] ") == "y")

    print("Running")