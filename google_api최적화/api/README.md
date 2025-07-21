# Historical Place Recognition API

사용자가 건물이나 유적지의 사진을 찍으면, GPS 정보를 기반으로 장소를 추정하고 AI를 활용해 역사적·철학적 정보를 제공하는 FastAPI 기반 백엔드 서비스입니다.

## 🏗️ 아키텍처

- **FastAPI**: REST API 서버
- **AWS S3**: 이미지 저장소
- **AWS SQS**: 비동기 처리 큐
- **AWS Lambda**: AI 분석 처리 (Rekognition + Bedrock)
- **Google Maps Platform API**: GPS → 장소명 변환

## 📋 요구사항

- Python 3.11+
- AWS 계정 및 자격 증명
- Google Cloud Platform 계정 및 Maps API 키

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론 (이미 완료됨)
cd /mnt/c/Users/DSO3/IdeaProjects/aws/api

# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 실제 API 키와 AWS 자격 증명을 입력하세요
```

### 2. 개발 환경 실행

```bash
# 스크립트를 사용한 실행 (권장)
./run.sh

# 또는 수동 실행
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Docker를 사용한 실행

```bash
# Docker Compose로 실행
docker-compose up --build

# 또는 Docker만 사용
docker build -t historical-api .
docker run -p 8000:8000 --env-file .env historical-api
```

## 📚 API 엔드포인트

### 기본 정보
- **Base URL**: `http://localhost:8000`
- **API Docs**: `http://localhost:8000/docs`
- **Health Check**: `GET /health`

### 주요 엔드포인트

#### 1. 사진 업로드 및 분석 시작
```http
POST /api/v1/upload-photo
Content-Type: multipart/form-data

Parameters:
- file: 이미지 파일 (JPEG, PNG, WebP)
- latitude: GPS 위도
- longitude: GPS 경도
```

**응답 예시:**
```json
{
  "request_id": "uuid-string",
  "status": "PENDING",
  "message": "Photo uploaded and analysis started",
  "place_info": {
    "place_name": "경복궁",
    "address": "서울특별시 종로구 사직로 161",
    "category": "관광명소"
  },
  "s3_url": "https://bucket.s3.region.amazonaws.com/photos/...",
  "processing_time": 1.23,
  "estimated_completion": "2-5 minutes"
}
```

#### 2. 분석 상태 조회
```http
GET /api/v1/analysis-status/{request_id}
```

#### 3. 장소 검색
```http
GET /api/v1/search-place?keyword=경복궁&latitude=37.5759&longitude=126.9769
```

## 🔧 환경 변수

`.env` 파일에 다음 변수들을 설정하세요:

```env
# AWS Configuration
AWS_REGION=ap-northeast-2
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=your-photo-bucket
SQS_QUEUE_URL=your-sqs-queue-url

# Google Maps API
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# Application Settings
DEBUG=True
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_IMAGE_TYPES=image/jpeg,image/png,image/webp
```

## 🏗️ 프로젝트 구조

```
api/
├── main.py                 # FastAPI 애플리케이션
├── config.py              # 설정 관리
├── models.py              # Pydantic 모델
├── requirements.txt       # Python 의존성
├── Dockerfile            # Docker 설정
├── docker-compose.yml    # Docker Compose 설정
├── run.sh               # 개발 실행 스크립트
├── services/            # 외부 서비스 연동
│   ├── s3_service.py    # AWS S3 서비스
│   ├── sqs_service.py   # AWS SQS 서비스
│   └── google_maps_service.py # Google Maps Platform API
└── utils/               # 유틸리티 함수
    ├── validators.py    # 입력 검증
    └── responses.py     # 응답 처리
```

## 🧪 테스트

```bash
# API 상태 확인
curl http://localhost:8000/health

# 사진 업로드 테스트 (예시)
curl -X POST "http://localhost:8000/api/v1/upload-photo" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_image.jpg" \
  -F "latitude=37.5759" \
  -F "longitude=126.9769"
```

## 🚀 배포

### EKS 배포 준비
1. Docker 이미지를 ECR에 푸시
2. Kubernetes 매니페스트 작성
3. EKS 클러스터에 배포

### AWS 리소스 설정
- S3 버킷 생성
- SQS 큐 생성
- Lambda 함수 배포 (별도 구현 필요)
- IAM 역할 및 정책 설정

## 📝 다음 단계

1. **Lambda 함수 구현**: Rekognition + Bedrock 연동
2. **데이터베이스 연동**: 분석 결과 영구 저장
3. **인증/인가**: JWT 토큰 기반 사용자 인증
4. **모니터링**: CloudWatch 로그 및 메트릭
5. **테스트 코드**: 단위 테스트 및 통합 테스트

## 🤝 기여

이슈나 개선사항이 있으시면 언제든 알려주세요!
