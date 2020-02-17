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
import asyncio

DISPLAY_STORAGE = True

def attachVolAWS(id, zone, size):
    volume = ec2.create_volume(Size=size, AvailabilityZone=zone)
    time.sleep(30)
    ec2.Instance(id).attach_volume(VolumeId=volume.id, Device='/dev/sdy')

def createAWSVM(vm, docker):
    #Create ssh key
    try:
        key_pair = ec2.create_key_pair(KeyName=vm[7].split(".")[0])
        keyPairOut = str(key_pair.key_material)
        outfile = open('keys/'+vm[7],'w')
        outfile.write(keyPairOut)
    except:
        pass
    #Create instance 
    response = ec2.create_instances(BlockDeviceMappings=[
        {
            'DeviceName': '/dev/xvda',
            'VirtualName': vm[2],
            'Ebs': {
                'DeleteOnTermination': True,
                'VolumeSize': int(vm[6]),
                #'standard'|'io1'|'gp2'|'sc1'|'st1'
                'VolumeType': vm[5] ,
            }
        },
    ],ImageId=vm[1], MinCount=1, MaxCount=1, InstanceType=vm[3], KeyName=vm[7].split(".")[0])
    id = response[0].instance_id
    return id

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

def loadInstancesFromFile():
    vms, docker = readFiles()
    for vm in vms:
        if vm[0]=='AWS':
            createAWSVM(vm, docker)

def rebootVMs():
    #aws
    instances = ec2.meta.client.describe_instance_status(IncludeAllInstances=True)['InstanceStatuses']
    ids = []
    for s in instances:
        ids.append(s['InstanceId'])
    ec2_c.reboot_instances(InstanceIds=ids)

def killVMs():
    #aws
    instances = ec2.meta.client.describe_instance_status(IncludeAllInstances=True)['InstanceStatuses']
    ids = []
    for s in instances:
        ids.append(s['InstanceId'])
    ec2_c.terminate_instances(InstanceIds=ids)

def debugFnc():
    return str('test')

def drawHeader(win):
    win.addstr(0,0,"***********************\n")
    win.addstr("Instance status\n")
    win.addstr(str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+'\n')
    win.addstr("***********************\n")

def drawFooter(win, msg):
    win.addstr('\n'+msg+'\n')
    win.addstr('\nc create VMs\n')
    win.addstr('r to reboot\n')
    win.addstr('t to terminate\n')
    win.addstr('q to quit\n')

def drawUpdateAWS(win):
    instances = ec2.meta.client.describe_instance_status(IncludeAllInstances=True)['InstanceStatuses']
    ids = [] 
    for s in instances:
        ids.append(s['InstanceId'])
    descriptions = ec2.meta.client.describe_instances(InstanceIds=ids)['Reservations']
    desc = {}
    for d in descriptions:
        for i in d['Instances']:
            desc[i['InstanceId']] = i
    for status in instances:
        y, x = win.getyx()
        win.addstr(y, x, status['InstanceId'])
        win.addstr(y, x+24, status['InstanceState']['Name']+'\n')
        if status['InstanceId'] in desc.keys():
            y, x = win.getyx()
            win.addstr(y, x+4, 'System: '+desc[status['InstanceId']]['ImageId']+'\n')
            win.addstr(y+1, x+4, 'Type: '+desc[status['InstanceId']]['InstanceType']+'\n')
            if DISPLAY_STORAGE:
                for block in desc[status['InstanceId']]['BlockDeviceMappings']:
                    win.addstr(y+2, x+4, 'Storage: '+str(ec2.Volume(block['Ebs']['VolumeId']).size)+'GB\n')
            win.addstr('\n')

def main(win):
    key=""
    msg=""
    win.clear()                
    while 1:          
        try:                 
            win.timeout(100)          
            key = win.getch()         
            win.clear()     

            #Draw VM information
            drawHeader(win)
            drawUpdateAWS(win)
            drawFooter(win, msg)

            #debug
            #win.addstr('key: '+str(key)+'\n')
            if key == 113:
                break           
            elif key == 102:
                msg = debugFnc()
            elif key == 99:
                try:
                    loadInstancesFromFile()
                    msg = "Created new instances"
                except Exception as e:
                    msg = "Error creating instance: "+str(e)
            elif key == 114:
                try:
                    rebootVMs()
                    msg = "Rebooting instances"
                except Exception as e:
                    msg = "Failed to reboot instances "+e
            elif key == 116:
                try:
                    killVMs()
                    msg = "Terminating instances"
                except Exception as e:
                    msg = "Failed to terminate instances "+e
            elif key > 0:
                msg = ""
            
        except Exception as e:
            win.clear()
            win.addstr("Error, q to quit\n")
            win.addstr(str(e))
            if key == 113:
                break    
            pass         


def printUpdate(vms):
    os.system('clear')
    for vm in vms:
        print(vm)
    print('q to quit')

if __name__ == "__main__":

    global ec2_c 
    ec2_c = boto3.client('ec2', region_name='us-east-1')
    global ec2
    ec2 = boto3.resource('ec2', region_name='us-east-1')
    curses.wrapper(main)

    '''
    instances = ec2.meta.client.describe_instance_status(IncludeAllInstances=True)['InstanceStatuses']
    ids = []
    for s in instances:
        ids.append(s['InstanceId'])
    descriptions = ec2.meta.client.describe_instances(InstanceIds=ids)['Reservations']
    for r in descriptions:
        for i in r['Instances']:
            print(i['InstanceId'])
            print(i['ImageId'])
            print(i['InstanceType'])
            for block in i['BlockDeviceMappings']:
                print(ec2.Volume(block['Ebs']))
                print(ec2.Volume(block['Ebs']['VolumeId']).size)
    for r in descriptions:
        for i in r['Instances']:
            print(i['ImageId'])
            print(i['InstanceId'])
            print(i['InstanceType'])
            print()
    '''