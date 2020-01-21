#!/usr/bin/python3

import os, uuid
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

if __name__ == "__main__":
	try:
		# Retrieve the connection string for use with the application. 
		connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')

		# Create the BlobServiceClient object which will be used to reference a container client
		blob_service_client = BlobServiceClient.from_connection_string(connect_str)

		# List all containers
		all_containers = blob_service_client.list_containers(include_metadata=True)
		for container in all_containers:
			print("\nContainer: " + container['name'])
			containerName = container['name']

			container_client = ContainerClient.from_connection_string(connect_str, container_name=containerName)

			print("Listing blobs...")
			# List the blobs in the container
			blob_list = container_client.list_blobs()
			for blob in blob_list:
				print("\t" + blob.name)

		print("\n")
	except Exception as ex:
		print('Exception:')
		print(ex)
