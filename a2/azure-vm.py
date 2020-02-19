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

#Useful example
#https://github.com/Azure-Samples/virtual-machines-python-manage/blob/master/example.py
#https://stackoverflow.com/questions/33271570/how-to-create-a-vm-with-a-custom-image-using-azure-sdk-for-python

#https://docs.microsoft.com/en-us/azure/python/python-sdk-azure-authenticate
#https://docs.microsoft.com/en-us/python/api/overview/azure/virtualmachines?view=azure-python

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

def createAzureVM(compute_client, network_client, resource_client, vm, docker):
    try:
        # Create a NIC
        resourceGroup = 'cis4010A2'
        nic = create_nic(network_client, resourceGroup, vm[2])
        # Create Linux VM
        print('\nCreating Linux Virtual Machine')
        vm_parameters = create_vm_parameters(nic.id, vm)
        async_vm_creation = compute_client.virtual_machines.create_or_update('cis4010A2', vm[2], vm_parameters)
        async_vm_creation.wait()

        # Create managed data disk
        print('\nCreate (empty) managed Data Disk')
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
        print('\nGet Virtual Machine by Name')
        virtual_machine = compute_client.virtual_machines.get(
            resourceGroup,
            vm[2]
        )

        # Attach data disk
        print('\nAttach Data Disk')
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
 
    except CloudError:
        print('A VM operation failed:\n{}'.format(traceback.format_exc()))
    else:
        print('All example operations completed successfully!')


def create_nic(network_client, resourceGroup, uid):
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

if __name__ == "__main__":
    #client = get_client_from_auth_file(ComputeManagementClient, auth_path='credentials.json')
    #network = get_client_from_auth_file(NetworkManagementClient, auth_path='credentials.json')

    compute_client = get_client_from_auth_file(ComputeManagementClient, auth_path='credentials.json')
    network_client = get_client_from_auth_file(NetworkManagementClient, auth_path='credentials.json')
    resource_client = get_client_from_auth_file(ResourceManagementClient, auth_path='credentials.json')

    vms, docker = readFiles()
    for vm in vms:
        if (vm[0]=='AZURE'):
            createAzureVM(compute_client, network_client, resource_client, vm, docker)

    '''

    #az vm list-ip-addresses -o table
    #az vm image list
    for vm in client.virtual_machines.list_all():
        print(vm.name)
        print(vm.hardware_profile)
        print(vm.network_profile)
        print(vm.network_profile.network_interfaces)
        print(vm)
        #print(vm.network_profile.network_interface)
    '''

#useful
'''
        # Delete Resource group and everything in it
        print('\nDelete Resource Group')
        delete_async_operation = resource_client.resource_groups.delete(
            GROUP_NAME)
        delete_async_operation.wait()
        print("\nDeleted: {}".format(GROUP_NAME))

        # Detach data disk
        print('\nDetach Data Disk')
        data_disks = virtual_machine.storage_profile.data_disks
        data_disks[:] = [
            disk for disk in data_disks if disk.name != 'mydatadisk1']
        async_vm_update = compute_client.virtual_machines.create_or_update(
            GROUP_NAME,
            VM_NAME,
            virtual_machine
        )
        virtual_machine = async_vm_update.result()

        # Deallocating the VM (in preparation for a disk resize)
        print('\nDeallocating the VM (to prepare for a disk resize)')
        async_vm_deallocate = compute_client.virtual_machines.deallocate(
            GROUP_NAME, VM_NAME)
        async_vm_deallocate.wait()

        # Increase OS disk size by 10 GB
        print('\nUpdate OS disk size')
        os_disk_name = virtual_machine.storage_profile.os_disk.name
        os_disk = compute_client.disks.get(GROUP_NAME, os_disk_name)
        if not os_disk.disk_size_gb:
            print(
                "\tServer is not returning the OS disk size, possible bug in the server?")
            print("\tAssuming that the OS disk size is 30 GB")
            os_disk.disk_size_gb = 30

        os_disk.disk_size_gb += 10

        async_disk_update = compute_client.disks.create_or_update(
            GROUP_NAME,
            os_disk.name,
            os_disk
        )
        async_disk_update.wait()

        # Start the VM
        print('\nStart VM')
        async_vm_start = compute_client.virtual_machines.start(
            GROUP_NAME, VM_NAME)
        async_vm_start.wait()

        # Restart the VM
        print('\nRestart VM')
        async_vm_restart = compute_client.virtual_machines.restart(
            GROUP_NAME, VM_NAME)
        async_vm_restart.wait()

        # Stop the VM
        print('\nStop VM')
        async_vm_stop = compute_client.virtual_machines.power_off(
            GROUP_NAME, VM_NAME)
        async_vm_stop.wait()

        # List VMs in subscription
        print('\nList VMs in subscription')
        for vm in compute_client.virtual_machines.list_all():
            print("\tVM: {}".format(vm.name))

        # List VM in resource group
        print('\nList VMs in resource group')
        for vm in compute_client.virtual_machines.list(GROUP_NAME):
            print("\tVM: {}".format(vm.name))

        # Delete VM
        print('\nDelete VM')
        async_vm_delete = compute_client.virtual_machines.delete(
            GROUP_NAME, VM_NAME)
        async_vm_delete.wait()

        # Create Windows VM
        print('\nCreating Windows Virtual Machine')
        # Recycling NIC of previous VM
        vm_parameters = create_vm_parameters(nic.id, VM_REFERENCE['windows'])
        async_vm_creation = compute_client.virtual_machines.create_or_update(
            GROUP_NAME, VM_NAME, vm_parameters)
        async_vm_creation.wait()
'''