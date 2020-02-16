#!/usr/bin/python3

#boto3 vm info
#https://python.gotrained.com/aws-ec2-management-python-boto3/

import time
import string
import json
import csv
import decimal
import boto3
import os

from botocore.exceptions import ClientError

def readFiles():
    vms = []
    docker = {}
    with open('data/vm.csv') as csvFile:
        reader = csv.reader(csvFile)
        #Skip header
        next(reader, None)
        for row in reader:
            vms.append(row)
    
    with open('data/docker.csv') as csvFile:
        reader = csv.reader(csvFile)
        #Skip header
        next(reader, None)
        for row in reader:
            name = row.pop(0)
            docker[name] = row
    return vms, docker


def createAWSVM(ec2, vm, docker):
    print("Creating / Starting: "+vm[2])
    #Create ssh key
    outfile = open('keys/'+vm[7],'w')
    key_pair = ec2.create_key_pair(KeyName='myKey')
    keyPairOut = str(key_pair.key_material)
    outfile.write(keyPairOut)

    #Create instance 
    ec2.create_instances(ImageId=vm[1], MinCount=1, MaxCount=1, InstanceType=vm[3], KeyName='myKey')

if __name__ == "__main__":

    print("""
************
Welcome
************""")
    ec2 = boto3.client('ec2', region_name='us-east-1')
    ec2_resource = boto3.resource('ec2', region_name='us-east-1')

    vms, docker = readFiles()
    for vm in vms:
        if vm[0]=='AWS':
            createAWSVM(ec2_resource, vm, docker)


