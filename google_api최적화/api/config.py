import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # AWS Configuration
    AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
    SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")
    
    # Google Maps API
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
    
    # Application Settings
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    ALLOWED_IMAGE_TYPES = os.getenv("ALLOWED_IMAGE_TYPES", "image/jpeg,image/png,image/webp").split(",")
    
    # API Settings
    API_V1_PREFIX = "/api/v1"
    PROJECT_NAME = "Historical Place Recognition API"
    VERSION = "1.0.0"

settings = Settings()
