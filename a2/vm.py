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
from multiprocessing import Process


DISPLAY_STORAGE = True
AWS_KEY = 'keys/testing6.pem'
AZURE_PUB_KEY = 'keys/azureKey.pub'
AZURE_KEY = 'keys/azureKey'

awsos = {}
awsos['ami-0a887e401f7654935'] = 'Amazon Linux'
awsos['ami-0e2ff28bfb72a4e45'] = 'Amazon Linux'
awsos['ami-0c322300a1dd5dc79'] = 'Red Hat'
awsos['ami-0df6cfabfbe4385b7'] = 'SUSE Linux'
awsos['ami-07ebfd5b3428b6f4d'] = 'Ubuntu Server'

#region [rgba(100,202,240,0.1)] Docker
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
        
def runDockerPsAzure(ip, key):
    return runDockerPs(ip, 'adminL0gin', key)
#endregion 

#region [rgba(160,32,240,0.1)] AWS
#TODO docker
#https://hackernoon.com/running-docker-on-aws-ec2-83a14b780c56?fbclid=IwAR0rUTEbORAjIquWMWI1DVyVWJ-1cLpWV5WkuBbGQjCT8PGYGhbqRH6cjdU

def attachVolAWS(id, zone, size):
    volume = ec2.create_volume(Size=size, AvailabilityZone=zone)
    time.sleep(30)
    ec2.Instance(id).attach_volume(VolumeId=volume.id, Device='/dev/sdy')

def createAWSVM(win, vm, docker):
    win.addstr('\n\nCreating AWS VM: '+vm[2]+'\n')
    win.refresh()
    #Create ssh key
    try:
        win.addstr('Creating key: '+vm[7]+'\n')
        win.refresh()
        key_pair = ec2.create_key_pair(KeyName=vm[7].split(".")[0])
        keyPairOut = str(key_pair.key_material)
        outfile = open('keys/'+vm[7],'w')
        outfile.write(keyPairOut)
    except:
        win.addstr('Key already exists\n')
        win.refresh()
        pass

    #Create instance 
    win.addstr('Creating VM instance\n')
    win.refresh()
    script = buildDockerScript(vm[2], awsos[vm[1]], docker, False)
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
    ],ImageId=vm[1], MinCount=1, MaxCount=1, InstanceType=vm[3], KeyName=vm[7].split(".")[0], UserData=script)
    id = response[0].instance_id
    return id

def killAWS():
    instances = ec2.meta.client.describe_instance_status(IncludeAllInstances=True)['InstanceStatuses']
    ids = []
    for s in instances:
        ids.append(s['InstanceId'])
    if len(ids) > 0:
        ec2_c.terminate_instances(InstanceIds=ids)

def rebootAWS():
    instances = ec2.meta.client.describe_instance_status(IncludeAllInstances=True)['InstanceStatuses']
    ids = []
    for s in instances:
        ids.append(s['InstanceId'])
    ec2_c.reboot_instances(InstanceIds=ids)

#endregion

#region [rgba(100,200,0,0.1)] AZURE
#Keyvault doc
#https://docs.microsoft.com/en-us/azure/virtual-machines/linux/key-vault-setup

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

dockerDeployments = []

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
    #async_vnet_creation.wait()

    # Create Subnet
    async_subnet_creation = network_client.subnets.create_or_update(
        resourceGroup,
        uid+'-vnet',
        uid+'-snet',
        {'address_prefix': '10.0.0.0/24'}
    )
    subnet_info = async_subnet_creation.result()

    public_ip_creation = network_client.public_ip_addresses.create_or_update(
        'cis4010A2', 
        uid+'-pub-ip',
        {
            'location': 'eastus'
        }
    )
    pub_ip = public_ip_creation.result()

    # Create NIC
    async_nic_creation = network_client.network_interfaces.create_or_update(
        resourceGroup,
        uid+'-nic',
        {
            'location': 'eastus',
            'ip_configurations': [{
                'name': uid+'-ip',
                "properties": {
                    "privateIPAllocationMethod": "Dynamic",
                    "publicIPAddress": {
                        "id": pub_ip.id
                    },
                },
                'subnet': {
                    'id': subnet_info.id
                }
            }]
        }
    )
    return async_nic_creation.result()

def create_vm_parameters(nic_id, vm):
    keyFile = open(AZURE_PUB_KEY,'r')
    return {
        'location': 'eastus',
        'os_profile': {
            'computer_name': vm[2],
            'admin_username': 'adminL0gin',
            'admin_password': 'myPa$$w0rd',
            'linux_configuration': {
                'disable_password_authentication': True,
                'ssh': {
                    'public_keys': [{
                        'path': '/home/adminL0gin/.ssh/authorized_keys',
                        'key_data': keyFile.read()
                    }]
                }
            },
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

def createAzureVM(win, vm, docker):
    win.addstr('\n\nCreating Azure VM: '+vm[2]+'\n')
    win.refresh()

    # Create a NIC
    resourceGroup = 'cis4010A2'
    id = ''
    win.addstr('Creating network interface\n')
    win.refresh()
    try:
        nic = create_nic(resourceGroup, vm[2])
        id = nic.id
    except:
        nic = network_client.network_interfaces.get('cis4010A2', vm[2]+'-nic')
        id = nic.id
        pass

    # Create Linux VM
    win.addstr('Creating machine\n')
    win.refresh()
    vm_parameters = create_vm_parameters(id, vm)
    async_vm_creation = compute_client.virtual_machines.create_or_update('cis4010A2', vm[2], vm_parameters)
    #async_vm_creation.wait()

    if vm[4] == 'Y':
        # Create managed data disk
        win.addstr('Creating disk\n')
        win.refresh()
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
        virtual_machine = compute_client.virtual_machines.get(
            resourceGroup,
            vm[2]
        )

        # Attach data disk
        win.addstr('Attaching disk\n')
        win.refresh()
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
    #async_disk_attach.wait()
    dockerDeployments.append(vm[2])

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
        s.sendline('sudo nohup ./script.sh &')
        s.prompt()
        s.logout()
        return 'success'

def killAzure():
    for vm in compute_client.virtual_machines.list_all():
        compute_client.virtual_machines.delete('cis4010A2', vm.name)

def rebootAzure():
    for vm in compute_client.virtual_machines.list_all():
        compute_client.virtual_machines.restart('cis4010A2', vm.name)
#endregion

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

def loadInstancesFromFile(win):
    vms, docker = readFiles()
    for vm in vms:
        if vm[0]=='AWS':
            createAWSVM(win, vm, docker)
        elif (vm[0]=='AZURE'):
            createAzureVM(win, vm, docker)

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
    win.addstr('d to view docker\n')
    win.addstr('r to reboot\n')
    win.addstr('t to terminate\n')
    win.addstr('q to quit\n')

def drawUpdateAWS(win):
    instances = ec2.meta.client.describe_instance_status(IncludeAllInstances=True)['InstanceStatuses']
    win.addstr('\n')
    ids = [] 
    for s in instances:
        ids.append(s['InstanceId'])
    descriptions = ec2.meta.client.describe_instances(InstanceIds=ids)['Reservations']
    desc = {}
    ip={}
    for d in descriptions:
        for i in d['Instances']:
            desc[i['InstanceId']] = i
            try:
                for a in i['NetworkInterfaces']:
                    ip[i['InstanceId']] = a['Association']['PublicIp']
            except:
                ip[i['InstanceId']] = 'None'
                pass
    for status in instances:
        y, x = win.getyx()
        win.addstr(y, x, status['InstanceId'])
        win.addstr(y, x+24, status['InstanceState']['Name'])
        ip_str = 'None'
        if status['InstanceId'] in ip:
            ip_str = ip[status['InstanceId']]
        win.addstr(y, x+48, ip_str+'\n')
        if status['InstanceId'] in desc.keys():
            y, x = win.getyx()
            try:
                win.addstr(y, x+4, 'System: '+awsos[desc[status['InstanceId']]['ImageId']]+'\n')
            except:
                pass
            win.addstr(y+1, x+4, 'Type: '+desc[status['InstanceId']]['InstanceType']+'\n')
            if DISPLAY_STORAGE:
                for block in desc[status['InstanceId']]['BlockDeviceMappings']:
                    win.addstr(y+2, x+4, 'Storage: '+str(ec2.Volume(block['Ebs']['VolumeId']).size)+'GB\n')
            win.addstr('\n')

def drawUpdateAzure(win):
    procs = []
    for vm in compute_client.virtual_machines.list_all():
        states = compute_client.virtual_machines.instance_view('cis4010A2', vm.name, expand='instanceView').statuses
        state = states[0].display_status
        if (len(states) > 1):
            state = states[1].display_status
            if vm.name in dockerDeployments:
                if 'running' in state:
                    try:
                        win.addstr('Installing docker images on: '+vm.name+'\n')
                        public_ip = network_client.public_ip_addresses.get('cis4010A2', vm.name+'-pub-ip').ip_address
                        p =  Process(target=installDockerAzure, args=(vm.name, public_ip, AZURE_KEY))
                        p.start()
                        procs.append(p)
                        dockerDeployments.remove(vm.name)
                    except Exception as  e:
                        win.addstr('Failed to install docker images on: '+vm.name+'\n'+e+'\n')
        y, x = win.getyx()
        win.addstr(y, x, vm.name)
        win.addstr(y, x+24, state)
        try:
            public_ip = network_client.public_ip_addresses.get('cis4010A2', vm.name+'-pub-ip')
            win.addstr(y, x+48, str(public_ip.ip_address)+'\n')
        except:
            win.addstr('\n')
            pass
        y, x = win.getyx()
        win.addstr('    OS: '+vm.storage_profile.image_reference.offer+'\n')
        win.addstr('    Type: '+vm.hardware_profile.vm_size+'\n')
        for disk in vm.storage_profile.data_disks:
            win.addstr('    Data disk: '+str(disk.disk_size_gb)+'GB\n')
        win.addstr('\n')
    win.addstr('\n')
    if (len(procs) > 0):
        win.addstr('Waiting for docker installs to finish\n')
        for p in procs:
            p.join()

def drawDockerUpdate(win):
    win.clear()
    win.addstr(0,0,"***********************\n")
    win.addstr("Docker Images\n")
    win.addstr("***********************\n\n")
    win.addstr('\n')
    win.refresh()

    #AWS
    instances = ec2.meta.client.describe_instance_status(IncludeAllInstances=False)['InstanceStatuses']
    ids = [] 
    for s in instances:
        ids.append(s['InstanceId'])
    descriptions = ec2.meta.client.describe_instances(InstanceIds=ids)['Reservations']
    for d in descriptions:
        for i in d['Instances']:
            try:
                for a in i['NetworkInterfaces']:
                    ip = a['Association']['PublicIp']
                    dockerPS = runDockerPsAWS(ip, AWS_KEY)
                    win.addstr(ip+'\n')
                    win.addstr(str(dockerPS).replace('\\r','').replace('\\n', '\n')+'\n\n')
                    win.refresh()
            except Exception as e:
                win.addstr(str(e)+'\n')
                pass
    #Azure
    for vm in compute_client.virtual_machines.list_all():
        states = compute_client.virtual_machines.instance_view('cis4010A2', vm.name, expand='instanceView').statuses
        if (len(states) > 1):
            state = states[1].display_status
            if 'running' in state:
                public_ip = network_client.public_ip_addresses.get('cis4010A2', vm.name+'-pub-ip').ip_address
                try:
                    win.addstr(vm.name +'@'+public_ip+'\n')
                    win.refresh()
                    dockerPS = runDockerPsAzure(public_ip, AZURE_KEY)
                    win.addstr(str(dockerPS).replace('\\r','').replace('\\n', '\n')+'\n\n')
                    win.refresh()
                except Exception as e:
                    win.addstr(str(e)+'\n')
                    pass

    win.addstr("Press Enter to continue...\n")
    while 1:          
        try:                 
            win.timeout(100)          
            key = win.getch()  
            if key == 10:
                return
        except:
            return

def main(win):
    key=""
    msg=""
    win.clear()                
    while 1:          
        try:                 
            win.timeout(1000)          
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
                exit(0)
                break           
            elif key == 102:
                msg = debugFnc()
            elif key == 100:
                drawDockerUpdate(win)
            elif key == 99:
                try:
                    loadInstancesFromFile(win)
                    msg = "Created new instances"
                except Exception as e:
                    msg = "Error creating instance: "+str(e)
                    win.timeout(5000)          
            elif key == 114:
                try:
                    rebootVMs()
                    msg = "Rebooting instances"
                except Exception as e:
                    msg = "Failed to reboot instances "+str(e)
            elif key == 116:
                try:
                    killVMs()
                    win.timeout(1000)          
                    msg = "Terminating instances"
                except Exception as e:
                    msg = "Failed to terminate instances "+str(e)
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
