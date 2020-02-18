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

from msrestazure.azure_exceptions import CloudError

from haikunator import Haikunator
haikunator = Haikunator()

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
STORAGE_ACCOUNT_NAME = haikunator.haikunate(delimiter='')

USERNAME = 'userlogin'
PASSWORD = 'Pa$$w0rd91'
VM_NAME = 'myTestVM'
NIC_ID = 'subscriptions/69100ca0-ae74-4e8e-a5fd-eca065fc83e0/resourceGroups/cis4010A2/providers/Microsoft.Network/networkInterfaces/cis4010Interface'

def createVM(client, param):
    try:
        return client.virtual_machines.create_or_update('cis4010A2', VM_NAME, param)
    except Exception as e:
        return e

if __name__ == "__main__":
    client = get_client_from_auth_file(ComputeManagementClient, auth_path='credentials.json')

    #az vm image list
    param={
            'location': LOCATION,
            'os_profile': {
                'computer_name': VM_NAME,
                'admin_username': USERNAME,
                'admin_password': PASSWORD
            },
            'hardware_profile': {
                'vm_size': 'Standard_DS1_v2'
            },
            'storage_profile': {
                'image_reference': {
                    'publisher': 'Canonical',
                    'offer': 'UbuntuServer',
                    'sku': '16.04.0-LTS',
                    'version': 'latest'
                },
            },
            'network_profile': {
                'network_interfaces': [{
                    'id': NIC_ID,
                }]
            },
        }
    print(createVM(client, param))
    '''

    '''