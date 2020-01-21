#!/usr/bin/python3

import boto3

def listAllContainers(s3):
    for bucket in s3.buckets.all():
        print(bucket.name)

if __name__ == "__main__":
    s3 = boto3.resource('s3')

    print("""Enter 'q' to quit\n
    1: All containers\n
    2 <container>: A specified container\n
    3 <file>: Look for file\n
    4 <file>: Download a file\n
    """)
    cmd = ''
    while (cmd != "q" and cmd != "Q"):
        cmd = input('')
        print("Running: "+cmd)
        if (cmd == "1"):
            listAllContainers(s3)
    
    print("Cleaning things up")
