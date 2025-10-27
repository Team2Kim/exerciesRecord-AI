# 📚 API 사용 예시

이 디렉토리에는 ExRecAI API를 사용하는 다양한 예시 코드가 포함되어 있습니다.

## 📁 파일 목록

- `api_examples.py` - Python 예시 코드
- `README.md` - 이 파일

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
pip install requests
```

### 2. 예시 실행

```bash
# 전체 예시 실행
python examples/api_examples.py

# 개별 함수 실행
# examples/api_examples.py 파일을 열어서
# main() 대신 개별 함수 호출
```

## 📝 예시 목록

### 1. 서버 헬스 체크
```python
from examples.api_examples import health_check_example

result = health_check_example()
```

### 2. 운동 일지 AI 분석
```python
from examples.api_examples import analyze_workout_log_example

result = analyze_workout_log_example()
```

### 3. 운동 루틴 AI 추천
```python
from examples.api_examples import recommend_workout_routine_example

result = recommend_workout_routine_example()
```

### 4. 운동 목록 조회
```python
from examples.api_examples import get_exercises_example

exercises = get_exercises_example()
```

### 5. 운동 검색
```python
from examples.api_examples import search_exercises_example

result = search_exercises_example()
```

### 6. 영상 검색
```python
from examples.api_examples import search_videos_example

result = search_videos_example()
```

## 🔧 커스터마이징

### 다른 서버 URL 사용

```python
# api_examples.py 파일 수정
BASE_URL = "https://your-server-url.com"

# 또는 환경변수 사용
import os
BASE_URL = os.getenv("EXRECAI_BASE_URL", "https://default-url.com")
```

### 다른 모델 사용

```python
# gpt-4o 모델 사용
response = requests.post(
    f"{BASE_URL}/api/workout-log/analyze?model=gpt-4o",
    json=workout_log
)
```

## 📊 응답 처리

### 성공 케이스
```python
if response.status_code == 200:
    result = response.json()
    print("✅ 성공!")
    print(result['ai_analysis'])
```

### 에러 처리
```python
try:
    response = requests.post(url, json=data, timeout=30)
    response.raise_for_status()  # HTTP 에러 확인
    result = response.json()
except requests.exceptions.RequestException as e:
    print(f"❌ 요청 실패: {e}")
except json.JSONDecodeError as e:
    print(f"❌ JSON 파싱 실패: {e}")
```

## 🌐 다른 언어에서 사용

### JavaScript
```javascript
fetch('https://your-server-url.com/api/workout-log/analyze', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    date: '2025-10-08',
    exercises: [...]
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

### cURL
```bash
curl -X POST "https://your-server-url.com/api/workout-log/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-10-08",
    "exercises": [...]
  }'
```

## 📌 주의사항

1. **OpenAI API 키**: AI 기능 사용 시 서버에 OPENAI_API_KEY 설정 필요
2. **타임아웃**: OpenAI API 호출은 시간이 걸릴 수 있으므로 timeout=30 권장
3. **Rate Limit**: API 호출 빈도는 적절히 유지해주세요
4. **에러 처리**: 항상 try-except로 에러를 처리하세요

## 🔗 관련 문서

- [전체 API 명세서](../API_SPECIFICATION.md)
- [시스템 흐름도](../SYSTEM_FLOW.md)
- [README](../README.md)


