#!/usr/bin/env python
# coding: utf-8

# In[1]:


import boto3

# Using AWS S3
# In[2]:


s3 = boto3.resource('s3')

# Print out bucket names
# In[3]:


for bucket in s3.buckets.all():
    print(bucket.name)

# Upload a new file
# In[4]:


data = open('/Users/debstacey/Teaching/CIS4010/Lectures/stream1.png', 'rb')
s3.Bucket('cis4010').put_object(Key='stream1.png', Body=data)

