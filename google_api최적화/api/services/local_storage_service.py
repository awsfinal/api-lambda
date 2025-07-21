"""
로컬 파일 저장 서비스 (AWS S3 대신 임시 사용)
"""
import os
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class LocalStorageService:
    def __init__(self):
        self.upload_dir = "static/uploads"
        self.ensure_upload_directory()
    
    def ensure_upload_directory(self):
        """업로드 디렉토리 생성"""
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
            logger.info(f"업로드 디렉토리 생성: {self.upload_dir}")
    
    async def upload_image(self, image_data: bytes, content_type: str, metadata: Dict[str, Any] = None) -> str:
        """
        이미지를 로컬에 저장하고 URL 반환
        """
        try:
            # 파일 확장자 결정
            ext_map = {
                'image/jpeg': '.jpg',
                'image/png': '.png',
                'image/webp': '.webp'
            }
            extension = ext_map.get(content_type, '.jpg')
            
            # 고유 파일명 생성
            filename = f"{uuid.uuid4()}{extension}"
            filepath = os.path.join(self.upload_dir, filename)
            
            # 파일 저장
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            # 메타데이터 저장 (JSON 파일로)
            if metadata:
                metadata_file = filepath + '.meta.json'
                import json
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        **metadata,
                        'upload_time': datetime.now().isoformat(),
                        'content_type': content_type,
                        'file_size': len(image_data)
                    }, f, indent=2, ensure_ascii=False)
            
            # 로컬 URL 반환
            local_url = f"http://localhost:8000/static/uploads/{filename}"
            
            logger.info(f"이미지 로컬 저장 완료: {filepath} ({len(image_data)} bytes)")
            return local_url
            
        except Exception as e:
            logger.error(f"로컬 이미지 저장 실패: {e}")
            raise Exception(f"Local storage failed: {str(e)}")

# 로컬 저장 서비스 인스턴스
local_storage_service = LocalStorageService()
