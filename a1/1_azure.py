#!/usr/bin/python3

import os, uuid
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

def uploadFile(client, containerName, fileName):
    try:
        f = open("data/"+fileName, 'rb')
        blob_client = client.get_blob_client(container=containerName, blob=fileName)
        blob_client.upload_blob(f)
    except Exception as e:
        print(containerName+" - "+fileName+ " already exists")

def createContainer(client, name):
    try:
        client.create_container(name)
    except Exception as e:
        print(name + ' already exists')

def init(client, connect_str):
    try:
        #create containers
        createContainer(client, "cis1300nolan")
        createContainer(client, "cis3110nolan")
        createContainer(client, "cis4010nolan")

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

    except Exception as e:
        print(e)
        exit(0)

def showAllObjIn(connect_str, containerName):
    try:
        print(containerName+":")
        container_client = ContainerClient.from_connection_string(connect_str, container_name=containerName)

        # List the blobs in the container
        blob_list = container_client.list_blobs()
        empty = True
        for blob in blob_list:
            empty = False
            print("\t" + blob.name)
        if (empty):
            print("\tempty")
        print('')
    except Exception as e:
        print(e)

def listAllContainers(client, connect_str):
    try:
        containers = client.list_containers(include_metadata=True)
        for container in containers:
            showAllObjIn(connect_str, container['name'])
    except Exception as e:
        print(e)

def searchForFile(client, connect_str, fileName, download):
    try:
        fileName = fileName.lower()
        containers = client.list_containers(include_metadata=True)
        for container in containers:
            container_client = ContainerClient.from_connection_string(connect_str, container_name=container['name'])
            blob_list = container_client.list_blobs()
            for blob in blob_list:
                if (fileName in blob.name.lower()):
                    if (not download):
                        print(blob.name+" in "+container['name'])
                    else:
                        with open("./"+blob.name, "wb") as file:
                            blob_client = client.get_blob_client(container=container['name'], blob=blob.name)
                            file.write(blob_client.download_blob().readall())
                            print('Downloaded: '+blob.name)
        print('')
    except Exception as e:
        print(e)



if __name__ == "__main__":
    connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    client = BlobServiceClient.from_connection_string(connect_str)

    init(client, connect_str)

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
            listAllContainers(client, connect_str)
        elif (cmd[0] == "2"):
            if (len(cmd)==1):
                print("Error no container\n")
                continue
            showAllObjIn(connect_str, cmd[1])
        elif (cmd[0] == "3" or cmd[0] == "4"):
            if (len(cmd)==1):
                print("Error no file\n")
                continue
            searchForFile(client, connect_str, cmd[1], cmd[0]=="4")