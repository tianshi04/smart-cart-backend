import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class R2Service:
    def __init__(self):
        self.account_id = settings.CLOUDFLARE_R2_ACCOUNT_ID
        self.access_key_id = settings.CLOUDFLARE_R2_ACCESS_KEY_ID
        self.secret_access_key = settings.CLOUDFLARE_R2_SECRET_ACCESS_KEY
        self.bucket_name = settings.CLOUDFLARE_R2_BUCKET_NAME
        
        # Cloudflare R2 endpoint URL format
        self.endpoint_url = f"https://{self.account_id}.r2.cloudflarestorage.com"

        self.s3_client = boto3.client(
            service_name='s3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name='auto' # R2 does not use regions in the traditional S3 sense
        )

    def upload_file(self, file_content: bytes, file_name: str, content_type: str) -> str | None:
        """
        Uploads a file to Cloudflare R2.
        :param file_content: The content of the file as bytes.
        :param file_name: The desired name of the file in the R2 bucket.
        :param content_type: The MIME type of the file (e.g., 'image/jpeg').
        :return: The object key (file name) if successful, None otherwise.
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_name,
                Body=file_content,
                ContentType=content_type
            )
            logger.info(f"File {file_name} uploaded successfully to R2.")
            return file_name
        except ClientError as e:
            logger.error(f"Failed to upload file {file_name} to R2: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during R2 upload: {e}")
            return None

    def delete_file(self, file_name: str) -> bool:
        """
        Deletes a file from Cloudflare R2.
        :param file_name: The name of the file (object key) to delete.
        :return: True if successful, False otherwise.
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_name
            )
            logger.info(f"File {file_name} deleted successfully from R2.")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file {file_name} from R2: {e}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during R2 deletion: {e}")
            return False

    def get_public_url(self, file_name: str) -> str:
        """
        Generates the public URL for a file stored in Cloudflare R2.
        This assumes you have a public domain configured for your R2 bucket.
        """
        # Use the configurable public URL from settings
        return f"{settings.CLOUDFLARE_R2_PUBLIC_URL}/{file_name}"

# Create a singleton instance of the R2Service
r2_service = R2Service()