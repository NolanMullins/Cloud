#!/usr/bin/python3

#boto3 vm info
#https://python.gotrained.com/aws-ec2-management-python-boto3/

import time
import string
import json
import csv
import boto3
import os
from botocore.exceptions import ClientError
import curses
import datetime

import azure
from azure.common.client_factory import get_client_from_auth_file
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import DiskCreateOption
from msrestazure.azure_exceptions import CloudError
from pexpect import pxssh
import getpass

'''
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo docker run -d -p 80:80 --name nginx nginx
'''
def installDockerAWS(ip, key):
    s = pxssh.pxssh()
    host = 'ec2'
    for num in ip.split('.'):
        host = host + '-' + num
    host = host + '.compute-1.amazonaws.com'
    user = 'ec2-user'
    print(host)
    if not s.login (server=host, username=user, ssh_key='keys/testing6.pem'):
        return "SSH session failed on login."+str(s)
    else:
        s.sendline('sudo yum update -y')
        s.prompt()
        s.sendline('sudo yum install -y docker')
        s.prompt()
        s.sendline('sudo service docker star')
        s.prompt()
        s.sendline('sudo docker run -d -p 80:80 --name nginx nginx')
        s.prompt()
        s.logout()
        return 'success'

#sudo ssh -i keys/testing6.pem ec2-user@ec2-54-89-226-82.compute-1.amazonaws.com
if __name__ == "__main__":
    print(installDockerAWS('54.89.226.82', 'keys/testting6.pem'))

    #if not s.login (server='localhost', username='myusername', password='mypassword'):
