import os, uuid, sys
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

try:
	# Get Container Names from command line
        number = len(sys.argv)
        x = 1
	while ( x < number ):
                containerName = sys.argv[x]
                x = x + 1
                print("Container: " + containerName)

		# Retrieve the connection string for use with the application. 
		connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')

		# Create the BlobServiceClient object which will be used to reference a container client
		blob_service_client = BlobServiceClient.from_connection_string(connect_str)

		container_client = ContainerClient.from_connection_string(connect_str, container_name=containerName)

		print("Listing blobs...")
		# List the blobs in the container
		blob_list = container_client.list_blobs()
		for blob in blob_list:
			print("\t" + blob.name)

except Exception as ex:
	print('Exception:')
	print(ex)
