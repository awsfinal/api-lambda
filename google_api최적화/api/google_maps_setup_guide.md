# Google Maps Platform API 설정 가이드

이 가이드는 Google Maps Platform API를 설정하고 이 애플리케이션에서 사용하는 방법을 설명합니다.

## 1. Google Cloud Platform 계정 생성

아직 Google Cloud Platform(GCP) 계정이 없다면, 다음 링크에서 계정을 생성하세요:
https://cloud.google.com/

## 2. 프로젝트 생성

1. Google Cloud Console에 로그인합니다.
2. 상단의 프로젝트 선택기를 클릭하고 "새 프로젝트"를 선택합니다.
3. 프로젝트 이름을 입력하고 "만들기"를 클릭합니다.

## 3. Google Maps Platform API 활성화

1. 생성한 프로젝트에서 "API 및 서비스" > "라이브러리"로 이동합니다.
2. 다음 API들을 검색하고 활성화합니다:
   - Maps JavaScript API
   - Geocoding API
   - Places API

## 4. API 키 생성

1. "API 및 서비스" > "사용자 인증 정보"로 이동합니다.
2. "사용자 인증 정보 만들기" > "API 키"를 클릭합니다.
3. 생성된 API 키를 복사합니다.

## 5. API 키 제한 설정 (권장)

보안을 위해 API 키에 제한을 설정하는 것이 좋습니다:

1. 생성된 API 키를 클릭합니다.
2. "애플리케이션 제한사항"에서 적절한 제한을 설정합니다 (예: HTTP 리퍼러, IP 주소).
3. "API 제한사항"에서 이 키가 사용할 수 있는 API를 위에서 활성화한 API들로 제한합니다.

## 6. 애플리케이션에 API 키 설정

1. 프로젝트 루트 디렉토리의 `.env` 파일에 API 키를 설정합니다:

```
GOOGLE_MAPS_API_KEY=your_api_key_here
```

2. `.env` 파일이 버전 관리 시스템에 포함되지 않도록 주의하세요.

## 7. 사용량 및 결제 설정

1. Google Cloud Console에서 "결제" 섹션으로 이동하여 결제 계정을 설정합니다.
2. "API 및 서비스" > "대시보드"에서 API 사용량을 모니터링할 수 있습니다.
3. 필요한 경우 사용량 한도 알림을 설정하여 예상치 못한 비용을 방지할 수 있습니다.

## 주요 API 기능

이 애플리케이션에서는 다음과 같은 Google Maps API 기능을 사용합니다:

1. **Geocoding API**: GPS 좌표를 주소로 변환 (역지오코딩)
2. **Places API**:
   - Nearby Search: 특정 좌표 주변의 장소 검색
   - Text Search: 키워드로 장소 검색
   - Place Details: 장소의 상세 정보 조회

## 문제 해결

- API 호출이 실패하는 경우 다음을 확인하세요:
  - API 키가 올바르게 설정되었는지 확인
  - 해당 API가 프로젝트에서 활성화되었는지 확인
  - API 키에 적용된 제한사항 확인
  - 결제 계정이 올바르게 설정되었는지 확인

- 자세한 오류 정보는 애플리케이션 로그와 Google Cloud Console의 "로그 탐색기"에서 확인할 수 있습니다.