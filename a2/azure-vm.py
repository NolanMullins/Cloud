#!/usr/bin/python3

import time
import string
import json
import csv
import os
import curses
import datetime
import traceback

import azure
from azure.common.client_factory import get_client_from_auth_file
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import DiskCreateOption

#Useful example
#https://github.com/Azure-Samples/virtual-machines-python-manage/blob/master/example.py
#https://stackoverflow.com/questions/33271570/how-to-create-a-vm-with-a-custom-image-using-azure-sdk-for-python

#https://docs.microsoft.com/en-us/azure/python/python-sdk-azure-authenticate
#https://docs.microsoft.com/en-us/python/api/overview/azure/virtualmachines?view=azure-python

# Azure Datacenter
LOCATION = 'eastus'

# Resource Group
GROUP_NAME = 'cis4010A2'

# Network
VNET_NAME = 'nolancis4010a2'
SUBNET_NAME = 'nolana2'

# VM
OS_DISK_NAME = 'azure-sample-osdisk'
#STORAGE_ACCOUNT_NAME = haikunator.haikunate(delimiter='')

USERNAME = 'userlogin'
PASSWORD = 'Pa$$w0rd91'
VM_NAME = 'myTestVM'
NIC_ID = 'subscriptions/69100ca0-ae74-4e8e-a5fd-eca065fc83e0/resourceGroups/cis4010A2/providers/Microsoft.Network/networkInterfaces/cis4010Interface'

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

def create_public_ip_address(network_client, name):
    public_ip_addess_params = {
        'location': 'eastus',
        'public_ip_allocation_method': 'Dynamic'
    }
    creation_result = network_client.public_ip_addresses.create_or_update(
        GROUP_NAME,
        name+'-ip',
        public_ip_addess_params
    )
    return creation_result.result()

def create_nic(network_client, vmName):
    subnet_info = network_client.subnets.get(
        GROUP_NAME, 
        'cis4010Interface', 
        'nolana2'
    )
    publicIPAddress = create_public_ip_address(network_client, vmName)
    '''
    publicIPAddress = network_client.public_ip_addresses.get(
        GROUP_NAME,
        'myIPAddress'
    )
    '''
    nic_params = {
        'location': LOCATION,
        'ip_configurations': [{
            'name': 'myIPConfig',
            'public_ip_address': publicIPAddress,
            'subnet': {
                'id': subnet_info.id
            }
        }]
    }
    creation_result = network_client.network_interfaces.create_or_update(
        GROUP_NAME,
        vmName+'-ip',
        nic_params
    )

    return creation_result.result()

def createAzureVM(client, network, vm, docker):
    
    '''
    nic = network.network_interfaces.get(
        GROUP_NAME, 
        'cis4010Interface'
    )
    '''
    nic = create_nic(network, vm[2])
    param={
            'location': 'eastus',
            'os_profile': {
                'computer_name': vm[2],
                'admin_username': 'adminL0gin',
                'admin_password': 'pa$$word'
            },
            'hardware_profile': {
                'vm_size': vm[3]
            },
            'storage_profile': {
                'image_reference': images[vm[1]]
            },
            'network_profile': {
                'network_interfaces': [{
                    'id': nic.id,
                }]
            },
        }
    try:
        return client.virtual_machines.create_or_update('cis4010A2', vm[2], param)
    except Exception as e:
        print('Error creating VM')
        print(e)
        return e

if __name__ == "__main__":
    client = get_client_from_auth_file(ComputeManagementClient, auth_path='credentials.json')
    network = get_client_from_auth_file(NetworkManagementClient, auth_path='credentials.json')

    vms, docker = readFiles()
    for vm in vms:
        if (vm[0]=='AZURE'):
            createAzureVM(client, network, vm, docker)

    #az vm list-ip-addresses -o table
    #az vm image list
    for vm in client.virtual_machines.list_all():
        print(vm.name)
        '''
        print(vm.hardware_profile)
        print(vm.network_profile)
        print(vm.network_profile.network_interfaces)
        print(vm)
        #print(vm.network_profile.network_interface)
        '''
