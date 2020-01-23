#!/usr/bin/python3

import string
import boto3
from botocore.exceptions import ClientError

def uploadFile(client, bucketName, fileName):
    f = open("data/"+fileName, 'rb')
    client.put_object(Bucket=bucketName, Key=fileName, Body=f)

def init():
    try:
        client = boto3.client('s3')
        #create containers
        client.create_bucket(Bucket="cis1300nolan")
        client.create_bucket(Bucket="cis3110nolan")
        client.create_bucket(Bucket="cis4010nolan")

        #upload files
        for i in range(1,5):
            name = "1300Assignment"+str(i)+".pdf"
            uploadFile(client, "cis1300nolan", name)

        for i in range(1,4):
            name = "3110Lecture"+str(i)+".pdf"
            uploadFile(client, "cis3110nolan", name)
        uploadFile(client, "cis3110nolan", "3110Assignment1.pdf")

        uploadFile(client, "cis4010nolan", "4010Assignment1.pdf")
        uploadFile(client, "cis4010nolan", "4010Lecture1.pdf")
        uploadFile(client, "cis4010nolan", "4010Lecture2.pdf")

    except ClientError as e:
        print(e)
        exit(0)

def showAllObjIn(s3, bucketName):
    try:
        print(bucketName+":")
        objects = s3.Bucket(bucketName).objects.all()
        empty = True
        for obj in objects:
            empty = False
            print("\t"+obj.key)
        if (empty):
            print("\tempty")
        print('')
    except ClientError as e:
        print(e)

def listAllContainers(s3):
    try:
        for bucket in s3.buckets.all():
            showAllObjIn(s3, bucket.name)
    except ClientError as e:
        print(e)

def searchForFile(s3, fileName, download):
    try:
        fileName = fileName.lower()
        for bucket in s3.buckets.all():
            objects = s3.Bucket(bucket.name).objects.all()
            for obj in objects:
                if (fileName in obj.key.lower()):
                    if (not download):
                        print(obj.key+" in "+bucket.name)
                    else:
                        client = boto3.client('s3')
                        client.download_file(bucket.name, obj.key, "./"+obj.key)
                        print('Downloaded: '+blob.name)
        print('')
    except ClientError as e:
        print(e)



if __name__ == "__main__":
    s3 = boto3.resource('s3')

    print("""Enter 'q' to quit\n
    1: All containers\n
    2 <container>: A specified container\n
    3 <file>: Look for file\n
    4 <file>: Download a file\n
    """)
    cmd = "init".split(' ')
    while (cmd[0] != "q" and cmd[0] != "Q"):
        cmd = input('Enter: ').split(' ')
        if (cmd[0] == "1"):
            listAllContainers(s3)
        elif (cmd[0] == "2"):
            if (len(cmd)==1):
                print("Error no container\n")
                continue
            showAllObjIn(s3, cmd[1])
        elif (cmd[0] == "3" or cmd[0] == "4"):
            if (len(cmd)==1):
                print("Error no file\n")
                continue
            searchForFile(s3, cmd[1], cmd[0]=="4")

    print("Cleaning things up")
