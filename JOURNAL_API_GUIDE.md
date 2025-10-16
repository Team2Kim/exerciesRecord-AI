# 운동 일지 조회 API 가이드

## 개요

클라이언트에서 받은 Authorization header와 date query parameter를 외부 API(`http://52.54.123.236/api/journals/by-date`)로 전달하여 특정 날짜의 운동 일지 데이터를 가져오는 기능입니다.

## API 명세

### 엔드포인트

```
GET /api/journals/by-date
```

### 요청 파라미터

#### Query Parameters
- **date** (필수): 조회할 날짜 (형식: `yyyy-MM-dd`)
  - 예: `2025-10-08`

#### Headers
- **Authorization** (필수): Bearer 토큰
  - 형식: `Bearer YOUR_ACCESS_TOKEN`
  - 예: `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### 요청 예시

#### cURL
```bash
# 로컬 개발
curl -X GET "http://localhost:3000/api/journals/by-date?date=2025-10-08" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# CloudType 배포
curl -X GET "https://your-cloudtype-url.com/api/journals/by-date?date=2025-10-08" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Python (httpx)
```python
import httpx

async def get_daily_log():
    # 로컬 개발
    url = "http://localhost:3000/api/journals/by-date"
    # CloudType 배포
    # url = "https://your-cloudtype-url.com/api/journals/by-date"
    
    headers = {
        "Authorization": "Bearer YOUR_ACCESS_TOKEN"
    }
    params = {
        "date": "2025-10-08"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        data = response.json()
        print(data)
```

#### JavaScript (fetch)
```javascript
const date = '2025-10-08';
const token = 'YOUR_ACCESS_TOKEN';

// 로컬 개발
const url = `http://localhost:3000/api/journals/by-date?date=${date}`;
// CloudType 배포
// const url = `https://your-cloudtype-url.com/api/journals/by-date?date=${date}`;

fetch(url, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
  .then(response => response.json())
  .then(data => console.log(data));
```

### 응답 형식

#### 성공 응답 (200 OK)
```json
{
  "success": true,
  "data": {
    "logId": 1,
    "date": "2025-10-08",
    "memo": "오늘은 하체 위주로 운동!",
    "exercises": [
      {
        "logExerciseId": 1,
        "intensity": "상",
        "exerciseTime": 20,
        "exercise": {
          "exerciseId": 15,
          "title": "스쿼트",
          "videoUrl": "http://...",
          "bodyPart": "하체",
          "exerciseTool": "맨몸"
        }
      }
    ]
  },
  "date": "2025-10-08"
}
```

#### 실패 응답

##### 404 Not Found (일지가 없는 경우)
```json
{
  "detail": "해당 날짜에 작성된 일지가 없습니다"
}
```

##### 401 Unauthorized (인증 실패)
```json
{
  "detail": "인증이 필요합니다. 유효한 토큰을 제공해주세요"
}
```

##### 500 Internal Server Error (서버 오류)
```json
{
  "detail": "운동 일지 조회 중 오류 발생: ..."
}
```

## 데이터 흐름

```
클라이언트
    ↓ (Authorization header + date query)
AI 서버 (FastAPI)
    ↓ (같은 header와 query 전달)
외부 API (http://52.54.123.236/api/journals/by-date)
    ↓ (운동 일지 데이터)
AI 서버
    ↓ (가공된 응답)
클라이언트
```

## 구현 세부 사항

### 1. `services/external_api.py`

`ExternalExerciseAPI` 클래스에 `get_daily_log_by_date` 메서드 추가:

```python
async def get_daily_log_by_date(
    self,
    date: str,
    access_token: str
) -> Dict[str, Any]:
    """특정 날짜의 운동 일지 조회"""
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    params = {
        "date": date
    }
    
    async with httpx.AsyncClient(timeout=self.timeout) as client:
        url = f"{self.journals_base_url}/by-date"
        response = await client.get(url, params=params, headers=headers)
        # ... 에러 처리
```

### 2. `main.py`

새로운 엔드포인트 추가:

```python
@app.get("/api/journals/by-date")
async def get_daily_log_by_date(
    date: str = Query(..., description="조회할 날짜 (형식: yyyy-MM-dd)"),
    authorization: str = Header(..., description="Bearer 토큰")
):
    """외부 API를 통해 특정 날짜의 운동 일지를 조회합니다."""
    
    # Bearer 토큰 추출
    access_token = authorization
    if authorization.startswith("Bearer "):
        access_token = authorization[7:]
    
    # 외부 API 호출
    result = await external_api.get_daily_log_by_date(
        date=date,
        access_token=access_token
    )
    # ... 응답 처리
```

## 테스트 방법

### 1. AI 서버 실행

#### 로컬 개발
```bash
python main.py
```

#### CloudType 배포
- Git push 후 자동 배포
- 또는 CloudType 대시보드에서 수동 배포

### 2. 테스트 스크립트 실행

`test_journal_api.py` 파일에서 토큰을 수정한 후:

```bash
# 로컬 테스트
python test_journal_api.py

# CloudType URL로 테스트 (스크립트 내 URL 수정 필요)
```

### 3. Swagger UI 테스트

#### 로컬 개발
```
http://localhost:3000/docs
```

#### CloudType 배포
```
https://your-cloudtype-url.com/docs
```

1. `/api/journals/by-date` 엔드포인트 선택
2. "Try it out" 버튼 클릭
3. `date` 입력 (예: 2025-10-08)
4. `authorization` 입력 (예: Bearer YOUR_TOKEN)
5. "Execute" 버튼 클릭

## 주의사항

1. **인증 토큰 필수**: 외부 API는 인증이 필요하므로, 유효한 Access Token을 제공해야 합니다.

2. **날짜 형식**: 반드시 `yyyy-MM-dd` 형식을 사용해야 합니다 (예: 2025-10-08).

3. **CORS 설정**: 프론트엔드에서 호출할 경우, CORS 설정이 이미 `allow_origins=["*"]`로 되어 있어 문제없습니다.

4. **타임아웃**: 외부 API 호출 시 30초 타임아웃이 설정되어 있습니다.

5. **캐싱 없음**: 운동 일지는 실시간 데이터이므로 캐싱을 하지 않습니다.

## 추가 기능 제안

### workout_analysis와 연동

`workout_analysis.py`에서 외부 API의 데이터를 사용하도록 확장할 수 있습니다:

```python
class WorkoutAnalysisService:
    def __init__(self, db: Session, use_external_api: bool = False):
        self.db = db
        self.use_external_api = use_external_api
    
    async def analyze_from_external_api(
        self,
        user_id: str,
        access_token: str,
        start_date: str,
        end_date: str
    ):
        """외부 API 데이터를 사용한 분석"""
        # 날짜 범위 내의 모든 일지 조회
        # 각 날짜별로 external_api.get_daily_log_by_date 호출
        # 분석 수행
        pass
```

## 문제 해결

### 연결 오류
- AI 서버가 실행 중인지 확인
- 외부 API 서버(52.54.123.236)가 정상 작동하는지 확인

### 401 Unauthorized
- Access Token이 유효한지 확인
- Bearer 접두사가 올바르게 포함되었는지 확인

### 404 Not Found
- 조회하려는 날짜에 실제로 운동 일지가 작성되었는지 확인
- 날짜 형식이 올바른지 확인 (yyyy-MM-dd)

## 관련 파일

- `services/external_api.py` - 외부 API 호출 로직
- `main.py` - FastAPI 엔드포인트
- `test_journal_api.py` - 테스트 스크립트
- `JOURNAL_API_GUIDE.md` - 이 가이드 문서

