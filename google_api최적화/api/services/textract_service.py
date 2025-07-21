"""
AWS Textract 서비스 - 이미지에서 텍스트 추출
"""
import boto3
import logging
from typing import List, Dict, Optional
from config import settings

logger = logging.getLogger(__name__)

class TextractService:
    def __init__(self):
        self.client = boto3.client(
            'textract',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
    
    async def extract_text_from_image(self, image_bytes: bytes) -> List[Dict[str, str]]:
        """
        이미지에서 텍스트 추출
        """
        try:
            response = self.client.detect_document_text(
                Document={'Bytes': image_bytes}
            )
            
            extracted_texts = []
            
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    text = block.get('Text', '').strip()
                    confidence = block.get('Confidence', 0)
                    
                    if text and confidence > 80:  # 80% 이상 신뢰도
                        extracted_texts.append({
                            'text': text,
                            'confidence': confidence,
                            'type': 'line'
                        })
            
            logger.info(f"텍스트 추출 완료: {len(extracted_texts)}개 텍스트")
            return extracted_texts
            
        except Exception as e:
            logger.error(f"Textract 텍스트 추출 실패: {e}")
            return []
    
    def filter_korean_business_names(self, texts: List[Dict[str, str]]) -> List[str]:
        """
        한국어 상호명으로 보이는 텍스트 필터링
        """
        import re
        
        business_keywords = [
            '카페', '커피', '식당', '마트', '편의점', '약국', '병원', 
            '은행', '미용실', '치킨', '피자', '중국집', '일식', '한식',
            '노래방', 'PC방', '학원', '서점', '옷가게', '신발', '가방'
        ]
        
        korean_pattern = re.compile(r'[가-힣]+')
        business_names = []
        
        for text_info in texts:
            text = text_info['text']
            
            # 한글이 포함되어 있고
            if korean_pattern.search(text):
                # 비즈니스 키워드가 포함되어 있거나
                if any(keyword in text for keyword in business_keywords):
                    business_names.append(text)
                # 또는 적절한 길이의 한글 텍스트
                elif 2 <= len(text) <= 20 and korean_pattern.match(text):
                    business_names.append(text)
        
        return business_names

# Mock 서비스 (AWS 설정이 없을 때 사용)
class MockTextractService:
    async def extract_text_from_image(self, image_bytes: bytes) -> List[Dict[str, str]]:
        """Mock 텍스트 추출"""
        # 실제로는 이미지를 분석하지만, 테스트용으로 샘플 데이터 반환
        return [
            {'text': '맛있는 김치찌개', 'confidence': 95.5, 'type': 'line'},
            {'text': '24시간 편의점', 'confidence': 88.2, 'type': 'line'},
            {'text': '커피전문점', 'confidence': 92.1, 'type': 'line'}
        ]
    
    def filter_korean_business_names(self, texts: List[Dict[str, str]]) -> List[str]:
        return [text['text'] for text in texts if '카페' in text['text'] or '편의점' in text['text'] or '찌개' in text['text']]

# 서비스 인스턴스 (AWS 설정에 따라 선택)
try:
    textract_service = TextractService()
except:
    logger.warning("AWS Textract 설정 실패, Mock 서비스 사용")
    textract_service = MockTextractService()
