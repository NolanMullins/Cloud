#!/usr/bin/python3

#boto3 vm info
#https://python.gotrained.com/aws-ec2-management-python-boto3/

import time
import string
import json
import csv
import decimal
import boto3

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


if __name__ == "__main__":

    print("""
************
Welcome
************""")
    ec2 = boto3.client('ec2')
    ec2_resource = boto3.resource('ec2')

    vms, docker = readFiles()

    print(vms)
    print(docker)
