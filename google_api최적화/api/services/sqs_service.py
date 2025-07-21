import boto3
import json
import uuid
from datetime import datetime
from botocore.exceptions import ClientError
from config import settings
import logging

logger = logging.getLogger(__name__)

class SQSService:
    def __init__(self):
        self.sqs_client = boto3.client(
            'sqs',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.queue_url = settings.SQS_QUEUE_URL

    async def send_analysis_request(self, s3_url: str, analysis_data: dict, request_id: str = None) -> str:
        """
        이미지 분석 요청을 SQS 큐에 전송합니다.
        """
        if not request_id:
            request_id = str(uuid.uuid4())
        
        message_body = {
            'request_id': request_id,
            's3_url': s3_url,
            'timestamp': datetime.now().isoformat(),
            'service_type': 'building_recognition',
            **analysis_data  # 추가 분석 데이터 포함
        }
        
        try:
            response = self.sqs_client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message_body),
                MessageAttributes={
                    'RequestType': {
                        'StringValue': 'building_recognition',
                        'DataType': 'String'
                    },
                    'RequestId': {
                        'StringValue': request_id,
                        'DataType': 'String'
                    },
                    'HasEXIF': {
                        'StringValue': str(analysis_data.get('exif_metadata', {}).get('has_exif', False)),
                        'DataType': 'String'
                    },
                    'HasGPS': {
                        'StringValue': str(analysis_data.get('exif_metadata', {}).get('has_gps', False)),
                        'DataType': 'String'
                    }
                }
            )
            
            logger.info(f"Building recognition request sent to SQS: {request_id}")
            return request_id
            
        except ClientError as e:
            logger.error(f"Failed to send message to SQS: {e}")
            raise Exception(f"Failed to queue analysis request: {str(e)}")

    async def get_queue_attributes(self) -> dict:
        """
        SQS 큐의 속성 정보를 가져옵니다.
        """
        try:
            response = self.sqs_client.get_queue_attributes(
                QueueUrl=self.queue_url,
                AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
            )
            return response.get('Attributes', {})
        except ClientError as e:
            logger.error(f"Failed to get queue attributes: {e}")
            return {}

sqs_service = SQSService()
