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

awsos = {}
awsos['ami-0a887e401f7654935'] = 'Amazon Linux'
awsos['ami-0e2ff28bfb72a4e45'] = 'Amazon Linux'
awsos['ami-0c322300a1dd5dc79'] = 'Red Hat'
awsos['ami-0df6cfabfbe4385b7'] = 'SUSE Linux'
awsos['ami-07ebfd5b3428b6f4d'] = 'Ubuntu Server'

AZURE_PUB_KEY = 'newKey.pub'
AZURE_KEY = 'newKey'
'''
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo docker run -d -p 80:80 --name nginx nginx
'''

def readFiles():
    vms = []
    docker = []
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
            docker.append(row)
    return vms, docker


def buildDockerScript(id, os, docker, flag):
    cmd = 'apt'
    if os == 'Amazon Linux':
        cmd = 'yum'
    script = "#!/bin/bash\n"
    script = script + 'sudo '+cmd+' update -y \n'
    if (flag):
        script = script + 'curl -sSL https://get.docker.com/ | sh \n'
    script = script + 'sudo '+cmd+' install -y docker \n'
    script = script + 'sudo service docker start \n'
    for image in docker:
        if image[0] == id:
            script = script + 'sudo docker run '+image[1]+' \n'
    return script

#Only use yum if using amazon linux
def installDockerAWS(ip, key):
    s = pxssh.pxssh()
    host = 'ec2'
    for num in ip.split('.'):
        host = host + '-' + num
    host = host + '.compute-1.amazonaws.com'
    user = 'ec2-user'
    if not s.login (server=host, username=user, ssh_key='keys/testing6.pem'):
        return "SSH session failed on login."+str(s)
    else:
        s.sendline('sudo yum update -y')
        s.prompt()
        s.sendline('sudo yum install -y docker')
        s.prompt()
        s.sendline('sudo service docker start')
        s.prompt()
        s.sendline('sudo docker run -d -p 80:80 --name nginx nginx')
        s.prompt()
        s.logout()
        return 'success'

def runDockerPs(host, user, key):
    result = ''
    s = pxssh.pxssh()
    if not s.login (server=host, username=user, ssh_key=key):
        return "SSH session failed on login."+str(s)
    else:
       s.sendline('sudo docker ps -a') 
       s.prompt()
       result = s.before
       s.logout()
       return result

def runDockerPsAWS(ip, key):
    host = 'ec2'
    for num in ip.split('.'):
        host = host + '-' + num
    host = host + '.compute-1.amazonaws.com'
    user = 'ec2-user'
    return runDockerPs(host, user, key)

def installDockerAzure(id, ip, key):
    s = pxssh.pxssh()
    vms, docker = readFiles()
    if not s.login (server=ip, username='adminL0gin', ssh_key=key):
        return "SSH session failed on login."+str(s)
    else:
        script = buildDockerScript(id, 'azure', docker, True)
        s.sendline("echo '"+script+"' > script.sh")
        s.prompt()
        s.sendline('sudo chmod +x script.sh')
        s.prompt()
        s.sendline('sudo nohup ./script.sh > result.log &')
        s.prompt()
        s.logout()
        '''
        s.sendline('sudo apt update -y')
        s.prompt()
        s.sendline('curl -sSL https://get.docker.com/ | sh')
        s.prompt()
        s.sendline('sudo apt install -y docker')
        s.prompt()
        s.sendline('sudo service docker start')
        s.prompt()
        for image in docker:
            if image[0] == id:
                print('running: '+image[1])
                s.sendline('sudo docker run '+image[1])
                s.prompt()
        s.logout()
        '''
        return 'success'

def runDockerPsAzure(ip, key):
    return runDockerPs(ip, 'adminL0gin', key)

#sudo ssh -i keys/testing6.pem ec2-user@ec2-54-89-226-82.compute-1.amazonaws.com
#sudo ssh -i keys/testing6.pem ec2-user@ec2-3-93-246-73.compute-1.amazonaws.com
if __name__ == "__main__":
    #print(installDockerAWS('54.89.226.82', 'keys/testting6.pem'))


    vms, docker = readFiles()
    print(buildDockerScript('debianVM', 'os', docker, True))
    cmd = 'az vm run-command invoke -g cis4010A2 -n otherVM --command-id RunShellScript --scripts \'sudo apt update -y && curl -sSL https://get.docker.com/ | sh && sudo apt install -y docker && sudo service docker start && sudo docker run mongo\''
    os.system(cmd)
    #result = runDockerPsAWS('18.207.209.164', 'keys/testing6.pem')
    #print(buildDockerScript('debian', 'azure', docker, True))
    #installDockerAzure('ubuntuVM', '52.170.86.56', 'keys/azureKey')
    #result = runDockerPsAzure('40.117.35.47', 'keys/azureKey')
    #print(str(result).replace('\\r','').replace('\\n', '\n'))
    #print(buildDockerScript('awsDockerVM', 'Amazon Linux', docker))
    #if not s.login (server='localhost', username='myusername', password='mypassword'):
