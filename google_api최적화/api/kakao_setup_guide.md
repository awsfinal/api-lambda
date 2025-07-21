# 카카오맵 API 권한 설정 가이드

## 현재 상태
- API 키: `bb53913dab59cc9256b91061c0cc3177`
- 앱 이름: "2훈2현"
- 오류: `App(2훈2현) disabled OPEN_MAP_AND_LOCAL service.`

## 해결 방법

### 1. 카카오 개발자 콘솔 접속
1. https://developers.kakao.com/ 접속
2. 로그인 후 **내 애플리케이션** 클릭
3. **"2훈2현"** 앱 선택

### 2. 플랫폼 설정 (필수)
```
앱 설정 → 플랫폼
- Web 플랫폼 추가
- 사이트 도메인: http://localhost:8000
```

### 3. 카카오맵 API 활성화 방법

#### 방법 A: 제품 설정에서 찾기
1. 좌측 메뉴 **"제품 설정"** 클릭
2. **"카카오맵"** 또는 **"Local API"** 찾기
3. **Web** 체크박스 활성화

#### 방법 B: API 설정에서 찾기
1. 좌측 메뉴 **"API 설정"** 클릭
2. **"Local"** 또는 **"Map"** 관련 API 찾기
3. 활성화 토글 ON

#### 방법 C: 앱 키 페이지에서 확인
1. **앱 설정** → **앱 키** 페이지
2. **REST API 키** 하단에 활성화된 서비스 목록 확인
3. **"Local API"** 또는 **"Map API"** 활성화

### 4. 만약 카카오맵 옵션이 안 보인다면

#### 신규 앱 생성 방법:
1. **새 애플리케이션 추가** 클릭
2. 앱 이름: "지도앱" (또는 원하는 이름)
3. 회사명: 개인 또는 회사명 입력
4. **앱 생성** 후 플랫폼 설정
5. **제품 설정**에서 **카카오맵** 활성화

#### 카카오맵 API 별도 신청:
- 일부 경우 카카오맵 API는 별도 승인이 필요할 수 있음
- 카카오 개발자 문의: https://devtalk.kakao.com/

### 5. 설정 완료 후 테스트
```bash
# API 키 테스트
curl -X GET "https://dapi.kakao.com/v2/local/search/keyword.json?query=경복궁" \
-H "Authorization: KakaoAK YOUR_NEW_API_KEY"
```

## 대안 방법

### JavaScript SDK 사용 (웹용)
```html
<script type="text/javascript" src="//dapi.kakao.com/v2/maps/sdk.js?appkey=YOUR_JAVASCRIPT_KEY"></script>
```

### 다른 지도 API 사용
- Google Maps API
- 네이버 지도 API
- OpenStreetMap

## 문제 해결 체크리스트
- [ ] 카카오 개발자 계정 로그인 확인
- [ ] 앱 "2훈2현" 선택 확인
- [ ] Web 플랫폼 추가 확인
- [ ] 제품 설정에서 카카오맵 찾기
- [ ] Local API 권한 활성화
- [ ] 설정 저장 후 몇 분 대기
- [ ] API 키로 테스트 실행
