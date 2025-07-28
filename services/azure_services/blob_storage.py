import os
import logging
from typing import Optional, List, Dict, Any
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class BlobStorageService:
    """Azure Blob Storage service with mock mode support"""
  
    def __init__(self, connection_string: Optional[str] = None, account_url: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.connection_string = connection_string or os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        self.account_url = account_url or os.getenv('AZURE_STORAGE_ACCOUNT_URL')
        self.blob_service_client = None
        self.mock_mode = False
        self.mock_containers = {}
        self.mock_blobs = {}
      
    async def initialize(self):
        """Initialize the blob storage service - THIS WAS MISSING!"""
        try:
            if self.connection_string:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    self.connection_string
                )
                logger.info("Initialized BlobStorageService with connection string")
            elif self.account_url:
                credential = DefaultAzureCredential()
                self.blob_service_client = BlobServiceClient(
                    account_url=self.account_url,
                    credential=credential
                )
                logger.info("Initialized BlobStorageService with managed identity")
            else:
                logger.warning("No Azure credentials provided. Running in mock mode.")
                self.mock_mode = True
              
        except Exception as e:
            logger.warning(f"Failed to initialize Azure Blob Storage: {e}. Running in mock mode.")
            self.mock_mode = True
  
    async def create_container(self, container_name: str) -> bool:
        """Create a container"""
        if self.mock_mode:
            self.mock_containers[container_name] = {
                'created': datetime.now(),
                'blobs': {}
            }
            logger.info(f"Mock: Created container '{container_name}'")
            return True
          
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            await asyncio.to_thread(container_client.create_container)
            logger.info(f"Created container '{container_name}'")
            return True
        except ResourceExistsError:
            logger.info(f"Container '{container_name}' already exists")
            return True
        except Exception as e:
            logger.error(f"Failed to create container '{container_name}': {e}")
            return False
  
    async def upload_blob(self, container_name: str, blob_name: str, data: bytes, 
                         content_type: str = "application/octet-stream") -> bool:
        """Upload a blob to a container"""
        if self.mock_mode:
            if container_name not in self.mock_containers:
                await self.create_container(container_name)
          
            self.mock_containers[container_name]['blobs'][blob_name] = {
                'data': data,
                'content_type': content_type,
                'size': len(data),
                'uploaded': datetime.now()
            }
            logger.info(f"Mock: Uploaded blob '{blob_name}' to container '{container_name}' ({len(data)} bytes)")
            return True
          
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, 
                blob=blob_name
            )
            await asyncio.to_thread(
                blob_client.upload_blob,
                data,
                content_type=content_type,
                overwrite=True
            )
            logger.info(f"Uploaded blob '{blob_name}' to container '{container_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to upload blob '{blob_name}': {e}")
            return False
  
    async def download_blob(self, container_name: str, blob_name: str) -> Optional[bytes]:
        """Download a blob from a container"""
        if self.mock_mode:
            if (container_name in self.mock_containers and 
                blob_name in self.mock_containers[container_name]['blobs']):
                data = self.mock_containers[container_name]['blobs'][blob_name]['data']
                logger.info(f"Mock: Downloaded blob '{blob_name}' from container '{container_name}'")
                return data
            else:
                logger.warning(f"Mock: Blob '{blob_name}' not found in container '{container_name}'")
                return None
              
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, 
                blob=blob_name
            )
            blob_data = await asyncio.to_thread(blob_client.download_blob)
            data = await asyncio.to_thread(blob_data.readall)
            logger.info(f"Downloaded blob '{blob_name}' from container '{container_name}'")
            return data
        except ResourceNotFoundError:
            logger.warning(f"Blob '{blob_name}' not found in container '{container_name}'")
            return None
        except Exception as e:
            logger.error(f"Failed to download blob '{blob_name}': {e}")
            return None
  
    async def list_blobs(self, container_name: str) -> List[Dict[str, Any]]:
        """List all blobs in a container"""
        if self.mock_mode:
            if container_name not in self.mock_containers:
                return []
          
            blobs = []
            for blob_name, blob_info in self.mock_containers[container_name]['blobs'].items():
                blobs.append({
                    'name': blob_name,
                    'size': blob_info['size'],
                    'content_type': blob_info['content_type'],
                    'last_modified': blob_info['uploaded']
                })
            logger.info(f"Mock: Listed {len(blobs)} blobs in container '{container_name}'")
            return blobs
          
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            blob_list = await asyncio.to_thread(container_client.list_blobs)
          
            blobs = []
            for blob in blob_list:
                blobs.append({
                    'name': blob.name,
                    'size': blob.size,
                    'content_type': blob.content_settings.content_type if blob.content_settings else None,
                    'last_modified': blob.last_modified
                })
          
            logger.info(f"Listed {len(blobs)} blobs in container '{container_name}'")
            return blobs
        except Exception as e:
            logger.error(f"Failed to list blobs in container '{container_name}': {e}")
            return []
  
    async def delete_blob(self, container_name: str, blob_name: str) -> bool:
        """Delete a blob from a container"""
        if self.mock_mode:
            if (container_name in self.mock_containers and 
                blob_name in self.mock_containers[container_name]['blobs']):
                del self.mock_containers[container_name]['blobs'][blob_name]
                logger.info(f"Mock: Deleted blob '{blob_name}' from container '{container_name}'")
                return True
            else:
                logger.warning(f"Mock: Blob '{blob_name}' not found in container '{container_name}'")
                return False
              
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, 
                blob=blob_name
            )
            await asyncio.to_thread(blob_client.delete_blob)
            logger.info(f"Deleted blob '{blob_name}' from container '{container_name}'")
            return True
        except ResourceNotFoundError:
            logger.warning(f"Blob '{blob_name}' not found in container '{container_name}'")
            return False
        except Exception as e:
            logger.error(f"Failed to delete blob '{blob_name}': {e}")
            return False
  
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        if self.mock_mode:
            total_containers = len(self.mock_containers)
            total_blobs = sum(len(container['blobs']) for container in self.mock_containers.values())
            total_size = sum(
                blob['size'] 
                for container in self.mock_containers.values() 
                for blob in container['blobs'].values()
            )
          
            return {
                'mode': 'mock',
                'containers': total_containers,
                'blobs': total_blobs,
                'total_size_bytes': total_size
            }
        else:
            return {
                'mode': 'azure',
                'service_url': self.blob_service_client.url if self.blob_service_client else None
            }

    async def upload_contract(self, contract_data):
      """Upload contract data to blob storage"""
      try:
          if self.mock_mode:
              self.logger.info(f"Mock mode: Would upload contract data")
              # Use attribute access instead of .get()
              contract_id = getattr(contract_data, 'id', 'unknown')
              return f"mock://contracts/{contract_id}.json"
          
          container_name = "contracts"
          # Use attribute access instead of .get()
          contract_id = getattr(contract_data, 'id', 'unknown')
          blob_name = f"{contract_id}.json"
          
          # Ensure container exists
          await self.create_container_if_not_exists(container_name)
          
          # Convert contract data to JSON string using model_dump()
          import json
          contract_json = json.dumps(contract_data.model_dump(), indent=2)
          
          # Upload the blob
          blob_client = self.blob_service_client.get_blob_client(
              container=container_name, 
              blob=blob_name
          )
          
          await blob_client.upload_blob(
              contract_json, 
              overwrite=True,
              content_type='application/json'
          )
          
          self.logger.info(f"Successfully uploaded contract {blob_name}")
          return f"https://{self.account_name}.blob.core.windows.net/{container_name}/{blob_name}"
          
      except Exception as e:
          self.logger.error(f"Error uploading contract: {str(e)}")
          if self.mock_mode:
              contract_id = getattr(contract_data, 'id', 'unknown')
              return f"mock://contracts/{contract_id}.json"
          raise

    async def upload_planogram(self, planogram_data):
      """Upload planogram data to blob storage"""
      try:
          if self.mock_mode:
              self.logger.info(f"Mock mode: Would upload planogram data")
              # Use attribute access instead of .get()
              planogram_id = getattr(planogram_data, 'id', 'unknown')
              return f"mock://planograms/{planogram_id}.json"
          
          container_name = "planograms"
          # Use attribute access instead of .get()
          planogram_id = getattr(planogram_data, 'id', 'unknown')
          blob_name = f"{planogram_id}.json"
          
          # Ensure container exists
          await self.create_container_if_not_exists(container_name)
          
          # Convert planogram data to JSON string using model_dump()
          import json
          planogram_json = json.dumps(planogram_data.model_dump(), indent=2)
          
          # Upload the blob
          blob_client = self.blob_service_client.get_blob_client(
              container=container_name, 
              blob=blob_name
          )
          
          await blob_client.upload_blob(
              planogram_json, 
              overwrite=True,
              content_type='application/json'
          )
          
          self.logger.info(f"Successfully uploaded planogram {blob_name}")
          return f"https://{self.account_name}.blob.core.windows.net/{container_name}/{blob_name}"
          
      except Exception as e:
          self.logger.error(f"Error uploading planogram: {str(e)}")
          if self.mock_mode:
              planogram_id = getattr(planogram_data, 'id', 'unknown')
              return f"mock://planograms/{planogram_id}.json"
          raise

    async def upload_audit_log(self, audit_data):
      """Upload audit log data to blob storage"""
      try:
          if self.mock_mode:
              self.logger.info(f"Mock mode: Would upload audit log data")
              audit_id = getattr(audit_data, 'id', 'unknown')
              return f"mock://audit-logs/{audit_id}.json"
          
          container_name = "audit-logs"
          audit_id = getattr(audit_data, 'id', 'unknown')
          blob_name = f"{audit_id}.json"
          
          await self.create_container_if_not_exists(container_name)
          
          import json
          audit_json = json.dumps(audit_data.model_dump(), indent=2)
          
          blob_client = self.blob_service_client.get_blob_client(
              container=container_name, 
              blob=blob_name
          )
          
          await blob_client.upload_blob(
              audit_json, 
              overwrite=True,
              content_type='application/json'
          )
          
          self.logger.info(f"Successfully uploaded audit log {blob_name}")
          return f"https://{self.account_name}.blob.core.windows.net/{container_name}/{blob_name}"
          
      except Exception as e:
          self.logger.error(f"Error uploading audit log: {str(e)}")
          if self.mock_mode:
              audit_id = getattr(audit_data, 'id', 'unknown')
              return f"mock://audit-logs/{audit_id}.json"
          raise

    async def upload_compliance_report(self, report_data):
        """Upload compliance report data to blob storage"""
        try:
            if self.mock_mode:
                self.logger.info(f"Mock mode: Would upload compliance report data")
                report_id = getattr(report_data, 'id', 'unknown')
                return f"mock://compliance-reports/{report_id}.json"
            
            container_name = "compliance-reports"
            report_id = getattr(report_data, 'id', 'unknown')
            blob_name = f"{report_id}.json"
            
            await self.create_container_if_not_exists(container_name)
            
            import json
            report_json = json.dumps(report_data.model_dump(), indent=2)
            
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, 
                blob=blob_name
            )
            
            await blob_client.upload_blob(
                report_json, 
                overwrite=True,
                content_type='application/json'
            )
            
            self.logger.info(f"Successfully uploaded compliance report {blob_name}")
            return f"https://{self.account_name}.blob.core.windows.net/{container_name}/{blob_name}"
            
        except Exception as e:
            self.logger.error(f"Error uploading compliance report: {str(e)}")
            if self.mock_mode:
                report_id = getattr(report_data, 'id', 'unknown')
                return f"mock://compliance-reports/{report_id}.json"
            raise

    async def upload_image(self, image_data):
      """Upload image data to blob storage"""
      try:
          if self.mock_mode:
              self.logger.info(f"Mock mode: Would upload image data")
              # Use attribute access instead of .get()
              image_id = getattr(image_data, 'id', 'unknown')
              return f"mock://images/{image_id}.jpg"
          
          container_name = "images"
          # Use attribute access instead of .get()
          image_id = getattr(image_data, 'id', 'unknown')
          # Determine file extension based on image type or default to jpg
          image_type = getattr(image_data, 'type', 'jpg')
          blob_name = f"{image_id}.{image_type}"
          
          # Ensure container exists
          await self.create_container_if_not_exists(container_name)
          
          # Handle different image data formats
          if hasattr(image_data, 'content'):
              # If image_data has binary content
              image_content = image_data.content
              content_type = f'image/{image_type}'
          else:
              # Convert image data to JSON string using model_dump()
              import json
              image_content = json.dumps(image_data.model_dump(), indent=2)
              content_type = 'application/json'
          
          # Upload the blob
          blob_client = self.blob_service_client.get_blob_client(
              container=container_name, 
              blob=blob_name
          )
          
          await blob_client.upload_blob(
              image_content, 
              overwrite=True,
              content_type=content_type
          )
          
          self.logger.info(f"Successfully uploaded image {blob_name}")
          return f"https://{self.account_name}.blob.core.windows.net/{container_name}/{blob_name}"
          
      except Exception as e:
          self.logger.error(f"Error uploading image: {str(e)}")
          if self.mock_mode:
              image_id = getattr(image_data, 'id', 'unknown')
              return f"mock://images/{image_id}.jpg"
          raise