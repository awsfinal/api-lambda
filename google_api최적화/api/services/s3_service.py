import boto3
import uuid
from datetime import datetime
from botocore.exceptions import ClientError
from config import settings
import logging

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.bucket_name = settings.S3_BUCKET_NAME

    async def upload_image(self, image_data: bytes, content_type: str, gps_coords: dict) -> str:
        """
        이미지를 S3에 업로드하고 URL을 반환합니다.
        """
        try:
            # 고유한 파일명 생성
            file_extension = self._get_file_extension(content_type)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photos/{timestamp}_{uuid.uuid4().hex[:8]}{file_extension}"
            
            # 메타데이터 설정
            metadata = {
                'latitude': str(gps_coords.get('latitude', '')),
                'longitude': str(gps_coords.get('longitude', '')),
                'upload_time': datetime.now().isoformat()
            }
            
            # S3에 업로드
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=image_data,
                ContentType=content_type,
                Metadata=metadata
            )
            
            # S3 URL 생성
            s3_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{filename}"
            
            logger.info(f"Image uploaded successfully: {s3_url}")
            return s3_url
            
        except ClientError as e:
            logger.error(f"Failed to upload image to S3: {e}")
            raise Exception(f"S3 upload failed: {str(e)}")

    def _get_file_extension(self, content_type: str) -> str:
        """
        Content-Type에서 파일 확장자를 추출합니다.
        """
        extension_map = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/webp': '.webp'
        }
        return extension_map.get(content_type, '.jpg')

    async def get_image_url(self, s3_key: str, expires_in: int = 3600) -> str:
        """
        S3 객체에 대한 presigned URL을 생성합니다.
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise Exception(f"Failed to generate image URL: {str(e)}")

s3_service = S3Service()
