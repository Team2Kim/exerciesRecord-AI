# CloudType 배포 설정 가이드

## 프로젝트 정보
- **프로젝트**: `chatlog`
- **서비스**: `exerciesrecord-ai` 
- **배포환경**: `main`
- **포트**: `3000`

## 환경 변수 설정

CloudType에서 다음 환경 변수들을 설정해주세요:

### 필수 환경 변수
```
PORT=3000
HOST=0.0.0.0
CLOUDTYPE=true
ENVIRONMENT=production
```

### 데이터베이스 설정 (필요시)
```
DATABASE_URL=sqlite:///./data/fitness.db
```

### 외부 API 설정 (필요시)
```
EXTERNAL_API_TIMEOUT=30
```

## 배포 명령어

### 시작 명령어
```bash
python main.py
```

### 또는 uvicorn 직접 실행
```bash
uvicorn main:app --host 0.0.0.0 --port 3000
```

## 포트 확인

서버가 정상적으로 시작되면 다음 메시지가 출력됩니다:
```
🚀 ExRecAI 서버를 시작합니다...
📍 서버 주소: http://0.0.0.0:3000
📚 API 문서: http://0.0.0.0:3000/docs
☁️ CloudType 배포 환경에서 실행 중...
```

## API 엔드포인트

배포 후 사용 가능한 주요 엔드포인트:

### 1. 운동 일지 조회 (새로 추가된 기능)
```
GET https://your-cloudtype-url.com/api/journals/by-date?date=2025-10-08
Headers: Authorization: Bearer YOUR_ACCESS_TOKEN
```

### 2. API 문서
```
https://your-cloudtype-url.com/docs
```

### 3. 건강 상태 확인
```
GET https://your-cloudtype-url.com/health
```

### 4. 운동 추천
```
POST https://your-cloudtype-url.com/api/recommend/external
```

## 테스트 방법

### 1. 로컬에서 CloudType URL 테스트
```python
import httpx

async def test_cloudtype():
    url = "https://your-cloudtype-url.com/api/journals/by-date"
    headers = {"Authorization": "Bearer YOUR_ACCESS_TOKEN"}
    params = {"date": "2025-10-08"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        print(response.json())
```

### 2. cURL 테스트
```bash
curl -X GET "https://your-cloudtype-url.com/api/journals/by-date?date=2025-10-08" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 주의사항

1. **포트 설정**: CloudType은 기본적으로 포트 3000을 사용합니다.
2. **CORS**: 이미 `allow_origins=["*"]`로 설정되어 있어 외부에서 접근 가능합니다.
3. **환경 변수**: `PORT` 환경 변수가 설정되면 자동으로 해당 포트를 사용합니다.
4. **리로드**: 프로덕션 환경에서는 자동 리로드가 비활성화됩니다.

## 문제 해결

### 포트 충돌
```bash
# 포트 사용 확인
lsof -i :3000
```

### 서버 시작 실패
```bash
# 의존성 설치 확인
pip install -r requirements.txt

# Python 버전 확인
python --version
```

### API 호출 실패
- CloudType URL이 올바른지 확인
- Authorization 헤더가 올바르게 설정되었는지 확인
- 외부 API 서버(52.54.123.236)가 정상 작동하는지 확인

## 로그 확인

CloudType 대시보드에서 서버 로그를 확인할 수 있습니다:
- 서버 시작 로그
- API 요청/응답 로그
- 에러 로그

## 업데이트 방법

코드 변경 후:
1. Git push
2. CloudType에서 자동 재배포 또는 수동 재배포
3. 서버 로그에서 정상 시작 확인
