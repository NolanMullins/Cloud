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

DISPLAY_STORAGE = True


#region [rgba(160,32,240,0.1)] AWS
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

def killAWS():
    instances = ec2.meta.client.describe_instance_status(IncludeAllInstances=True)['InstanceStatuses']
    ids = []
    for s in instances:
        ids.append(s['InstanceId'])
    ec2_c.terminate_instances(InstanceIds=ids)

def rebootAWS():
    instances = ec2.meta.client.describe_instance_status(IncludeAllInstances=True)['InstanceStatuses']
    ids = []
    for s in instances:
        ids.append(s['InstanceId'])
    ec2_c.reboot_instances(InstanceIds=ids)

#endregion

#region [rgba(100,200,0,0.1)] AZURE
debian = {
    "offer": "debian-10",
    "publisher": "Debian",
    "sku": "10",
    "urn": "Debian:debian-10:10:latest",
    "urnAlias": "Debian",
    "version": "latest"
}

redHat = {
    "offer": "RHEL",
    "publisher": "RedHat",
    "sku": "7-LVM",
    "urn": "RedHat:RHEL:7-LVM:latest",
    "urnAlias": "RHEL",
    "version": "latest"
}

ubuntu = {
    "offer": "UbuntuServer",
    "publisher": "Canonical",
    "sku": "18.04-LTS",
    "urn": "Canonical:UbuntuServer:18.04-LTS:latest",
    "urnAlias": "UbuntuLTS",
    "version": "latest"
}
images = {}
images['debian'] = debian
images['redHat'] = redHat
images['ubuntu'] = ubuntu

#https://docs.microsoft.com/en-us/python/api/azure-mgmt-network/azure.mgmt.network.v2019_11_01.operations.networkinterfacesoperations?view=azure-python
def create_nic(resourceGroup, uid):
    #create vnet
    async_vnet_creation = network_client.virtual_networks.create_or_update(
        resourceGroup,
        uid+'-vnet',
        {
            'location': 'eastus',
            'address_space': {
                'address_prefixes': ['10.0.0.0/16']
            }
        }
    )
    async_vnet_creation.wait()

    # Create Subnet
    async_subnet_creation = network_client.subnets.create_or_update(
        resourceGroup,
        uid+'-vnet',
        uid+'-snet',
        {'address_prefix': '10.0.0.0/24'}
    )
    subnet_info = async_subnet_creation.result()

    # Create NIC
    async_nic_creation = network_client.network_interfaces.create_or_update(
        resourceGroup,
        uid+'-nic',
        {
            'location': 'eastus',
            'ip_configurations': [{
                'name': uid+'-ip',
                'subnet': {
                    'id': subnet_info.id
                }
            }]
        }
    )
    return async_nic_creation.result()

def create_vm_parameters(nic_id, vm):
    return {
        'location': 'eastus',
        'os_profile': {
            'computer_name': vm[2],
            'admin_username': 'adminL0gin',
            'admin_password': 'myPa$$w0rd'
        },
        'hardware_profile': {
            'vm_size': vm[3]
        },
        'storage_profile': {
            'image_reference': images[vm[1]]
        },
        'network_profile': {
            'network_interfaces': [{
                'id': nic_id,
            }]
        },
    }

def createAzureVM(vm, docker):
    #resource_client = get_client_from_auth_file(ResourceManagementClient, auth_path='credentials.json')
    # Create a NIC
    resourceGroup = 'cis4010A2'
    id = ''
    try:
        nic = create_nic(resourceGroup, vm[2])
        id = nic.id
    except:
        nic = network_client.virtual_networks.get('cis4010A2', vm[2]+'-nic')
        id = nic.id
        pass
    # Create Linux VM
    #print('\nCreating Linux Virtual Machine')
    vm_parameters = create_vm_parameters(id, vm)
    async_vm_creation = compute_client.virtual_machines.create_or_update('cis4010A2', vm[2], vm_parameters)
    async_vm_creation.wait()

    # Create managed data disk
    #print('\nCreate (empty) managed Data Disk')
    async_disk_creation = compute_client.disks.create_or_update(
        resourceGroup,
        vm[2]+'-disk',
        {
            'location': 'eastus',
            'disk_size_gb': int(vm[6]),
            'creation_data': {
                'create_option': DiskCreateOption.empty
            }
        }
    )
    data_disk = async_disk_creation.result()

    # Get the virtual machine by name
    #print('\nGet Virtual Machine by Name')
    virtual_machine = compute_client.virtual_machines.get(
        resourceGroup,
        vm[2]
    )

    # Attach data disk
    #print('\nAttach Data Disk')
    virtual_machine.storage_profile.data_disks.append({
        'lun': 12,
        'name': vm[2]+'-disk',
        'create_option': DiskCreateOption.attach,
        'managed_disk': {
            'id': data_disk.id
        }
    })
    async_disk_attach = compute_client.virtual_machines.create_or_update(
        resourceGroup,
        virtual_machine.name,
        virtual_machine
    )
    async_disk_attach.wait()

    
def killAzure():
    deletedVMs = []
    for vm in compute_client.virtual_machines.list_all():
        deletedVMs.append(compute_client.virtual_machines.delete('cis4010A2', vm.name))
        network_client.virtual_networks.delete('cis4010A2', vm[2]+'-nic')
    for deleted in deletedVMs:
        deleted.wait()

def rebootAzure():
    vms = []
    for vm in compute_client.virtual_machines.list_all():
        vms.append(compute_client.virtual_machines.restart('cis4010A2', vm.name))
    for vm in vms:
        vm.wait()
#endregion

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
        elif (vm[0]=='AZURE'):
            createAzureVM(vm, docker)

def rebootVMs():
    rebootAWS()
    rebootAzure()

def killVMs():
    killAWS()
    killAzure()

def debugFnc():
    return str('test')

#region [rgba(80,0,0,0.2)] curses
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

def drawUpdateAzure(win):
    win.addstr('\n')
    for vm in compute_client.virtual_machines.list_all():
        win.addstr(vm.name+'\n')
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
            drawUpdateAzure(win)
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
#endregion

if __name__ == "__main__":

    global ec2_c 
    ec2_c = boto3.client('ec2', region_name='us-east-1')
    global ec2
    ec2 = boto3.resource('ec2', region_name='us-east-1')
    global compute_client
    compute_client = get_client_from_auth_file(ComputeManagementClient, auth_path='credentials.json')
    global network_client
    network_client = get_client_from_auth_file(NetworkManagementClient, auth_path='credentials.json')
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