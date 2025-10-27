# 📚 ExRecAI API 명세서

> AI 기반 운동 추천 및 일지 분석 시스템

**Base URL**: `https://port-0-exerciesrecord-ai-m09uz3m21c03af28.sel4.cloudtype.app`

---

## 📑 목차

- [인증](#인증)
- [AI 기반 운동 분석 API](#ai-기반-운동-분석-api)
  - [운동 일지 AI 분석](#1-운동-일지-ai-분석)
  - [운동 루틴 AI 추천](#2-운동-루틴-ai-추천)
- [기존 API](#기존-api)
- [응답 코드](#응답-코드)

---

## 인증

현재 API는 공개 API로 제공됩니다. 향후 인증 기능 추가 예정.

---

## 🤖 AI 기반 운동 분석 API

### 1. 운동 일지 AI 분석

OpenAI GPT-4o-mini를 활용한 운동 일지 분석 및 평가

#### **엔드포인트**
```
POST /api/workout-log/analyze
```

#### **요청 헤더**
```
Content-Type: application/json
```

#### **요청 파라미터**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `model` | string | 선택 | OpenAI 모델 (기본: `gpt-4o-mini`) |

**사용 가능한 모델**:
- `gpt-4o-mini` - 가장 저렴하고 빠름 (기본값)
- `gpt-4o` - 균형잡힌 성능
- `gpt-4` - 최고 품질

#### **요청 본문**
```json
{
  "logId": 3,
  "date": "2025-10-08",
  "memo": "근육을 추가한 후",
  "exercises": [
    {
      "logExerciseId": 8,
      "exercise": {
        "exerciseId": 1,
        "title": "팔굽혀펴기",
        "muscles": ["어깨세모근", "큰가슴근", "위팔세갈래근"],
        "videoUrl": "http://...",
        "trainingName": "팔 굽혀 펴기(매트)",
        "exerciseTool": "매트",
        "targetGroup": "유소년",
        "fitnessFactorName": "근력/근지구력",
        "fitnessLevelName": "중급",
        "trainingPlaceName": "실내"
      },
      "intensity": "상",
      "exerciseTime": 20
    }
  ]
}
```

#### **응답 (성공)**
```json
{
  "success": true,
  "ai_analysis": "안녕하세요! 운동 일지를 공유해주셔서 감사합니다...\n\n### 1. 전반적인 운동 평가\n- **강도**: ...\n- **시간**: ...\n- **다양성**: ...\n\n### 2. 타겟 근육 분석 및 효과\n...\n\n### 3. 좋은 점과 개선할 점\n...\n\n### 4. 다음 운동을 위한 구체적인 추천\n...\n\n### 5. 부상 예방을 위한 주의사항\n...",
  "basic_analysis": {
    "summary": "2025-10-08에 2개 운동을 총 40분간 수행했습니다.",
    "statistics": {
      "total_exercises": 2,
      "total_time": 40,
      "avg_time_per_exercise": 20.0,
      "intensity_distribution": {
        "상": 2,
        "중": 0,
        "하": 0
      },
      "intensity_percentage": {
        "상": 100.0,
        "중": 0.0,
        "하": 0.0
      },
      "body_parts_trained": {
        "하체": 2
      },
      "exercise_tools_used": {
        "매트": 2
      },
      "muscles_targeted": [
        "어깨세모근",
        "큰가슴근",
        "위팔세갈래근"
      ]
    },
    "insights": [
      "주요 타겟 근육: 어깨세모근, 위팔세갈래근, 큰가슴근",
      "운동 순서: '팔굽혀펴기' → '팔굽혀펴기'로 구성되어 있습니다.",
      "운동 메모: '근육을 추가한 후'"
    ],
    "recommendations": [
      "다음 운동은 중강도로 조절하여 과부하를 방지하세요.",
      "상체 운동을 추가하여 전신 균형을 맞춰보세요."
    ],
    "warnings": [
      "고강도 운동이 100.0%로 매우 높습니다. 근육 회복을 위해 충분한 휴식을 취하고 단백질 섭취를 늘리세요."
    ]
  },
  "model": "gpt-4o-mini",
  "date": "2025-10-08"
}
```

#### **응답 (실패)**
```json
{
  "success": false,
  "message": "OpenAI API 키가 설정되지 않았습니다.",
  "basic_analysis": {
    "summary": "...",
    "statistics": {...},
    "recommendations": [...]
  }
}
```

#### **cURL 예시**
```bash
curl -X POST "https://port-0-exerciesrecord-ai-m09uz3m21c03af28.sel4.cloudtype.app/api/workout-log/analyze?model=gpt-4o-mini" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-10-08",
    "memo": "근육을 추가한 후",
    "exercises": [...]
  }'
```

---

### 2. 운동 루틴 AI 추천

사용자의 운동 기록을 기반으로 맞춤 운동 루틴 생성

#### **엔드포인트**
```
POST /api/workout-log/recommend
```

#### **요청 파라미터**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `days` | integer | 선택 | 7 | 루틴 기간 (1-30일) |
| `frequency` | integer | 선택 | 4 | 주간 운동 빈도 (1-7회) |
| `model` | string | 선택 | gpt-4o-mini | OpenAI 모델 |

#### **요청 본문**
```json
{
  "date": "2025-10-08",
  "exercises": [
    {
      "exercise": {
        "title": "팔굽혀펴기",
        "muscles": ["어깨세모근", "큰가슴근", "위팔세갈래근"]
      },
      "intensity": "상",
      "exerciseTime": 20
    }
  ]
}
```

#### **응답 (성공)**
```json
{
  "success": true,
  "ai_routine": "## 운동 목표와 전체적인 방향성\n목표: 근육량 증가와 전신 균형을 위한 운동 루틴\n...\n\n## 주간 루틴 개요\n- **월요일**: 어깨, 팔\n- **화요일**: 하체, 코어\n...\n\n## 일별 상세 루틴\n\n### 월요일 (어깨, 팔)\n1. **덤벨 숄더 프레스**\n   - 세트: 4\n   - 횟수: 10-12\n   - 휴식시간: 60초\n...",
  "basic_summary": {
    "date": "2025-10-08",
    "total_exercises": 2,
    "summary": "2025-10-08에 2개 운동을 총 40분간 수행했습니다."
  },
  "routine_period": {
    "days": 7,
    "frequency": 4
  },
  "model": "gpt-4o-mini"
}
```

#### **cURL 예시**
```bash
curl -X POST "https://port-0-exerciesrecord-ai-m09uz3m21c03af28.sel4.cloudtype.app/api/workout-log/recommend?days=7&frequency=4" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-10-08",
    "exercises": [...]
  }'
```

---

### 3. AI 기반 운동 추천 (기존 분석 데이터 기반)

#### **엔드포인트**
```
GET /api/analysis/ai-recommendation/{user_id}
```

#### **요청 파라미터**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `user_id` | string | 필수 | - | 사용자 ID |
| `days` | integer | 선택 | 30 | 분석 기간 (1-365일) |
| `model` | string | 선택 | gpt-4o-mini | OpenAI 모델 |

#### **응답**
```json
{
  "user_id": "demo_user",
  "analysis_period": "최근 30일",
  "basic_analysis": {
    "total_workouts": 16,
    "total_time": 1500,
    "balance_score": 65.5,
    "overworked_parts": ["가슴"],
    "underworked_parts": ["등", "코어"]
  },
  "ai_recommendation": "당신의 운동 패턴을 분석한 결과...",
  "ai_success": true,
  "fallback_used": false
}
```

#### **cURL 예시**
```bash
curl "https://port-0-exerciesrecord-ai-m09uz3m21c03af28.sel4.cloudtype.app/api/analysis/ai-recommendation/demo_user?days=30"
```

---

## 🔄 기존 API

### 운동 추천 API

#### 외부 영상 기반 추천
```
POST /api/recommend/external
```

#### 향상된 추천 (영상 포함)
```
POST /api/recommend/enhanced?include_videos=true
```

#### 빠른 추천
```
GET /api/recommend/quick/{user_id}?goal=체력+향상&frequency=3&level=초급
```

### 운동 데이터베이스 API

#### 운동 목록 조회
```
GET /api/exercises?skip=0&limit=50&body_part=가슴&category=웨이트
```

#### 운동 검색
```
GET /api/exercises/search?q=벤치프레스&limit=20
```

#### 운동 상세 조회
```
GET /api/exercises/{exercise_id}
```

### 운동 영상 API

#### 영상 검색
```
GET /api/videos/search?keyword=벤치프레스&target_group=성인&page=0&size=10
```

#### 근육별 영상 검색
```
GET /api/videos/by-muscle?muscles=가슴,삼두&page=0&size=10
```

#### 인기 영상 조회
```
GET /api/videos/popular?target_group=성인&limit=10
```

### 운동 일지 분석 API

#### 운동 패턴 분석
```
GET /api/analysis/workout-pattern/{user_id}?days=30
```

#### 맞춤 인사이트
```
GET /api/analysis/insights/{user_id}?days=30
```

#### 종합 분석
```
GET /api/analysis/comprehensive/{user_id}?days=30
```

### 시스템 API

#### 헬스 체크
```
GET /health
```

**응답**:
```json
{
  "status": "healthy",
  "database_connected": true,
  "total_exercises": 20,
  "total_users": 3,
  "version": "1.0.0",
  "uptime": "2시간 15분"
}
```

---

## 🔢 응답 코드

| 코드 | 설명 |
|------|------|
| 200 | 성공 |
| 400 | 잘못된 요청 |
| 404 | 리소스를 찾을 수 없음 |
| 500 | 서버 내부 오류 |

---

## 📝 요청/응답 예시

### 1. 운동 일지 분석 요청 예시

**Python**
```python
import requests

url = "https://port-0-exerciesrecord-ai-m09uz3m21c03af28.sel4.cloudtype.app/api/workout-log/analyze"
data = {
    "date": "2025-10-08",
    "memo": "근육을 추가한 후",
    "exercises": [
        {
            "exercise": {
                "title": "팔굽혀펴기",
                "muscles": ["어깨세모근", "큰가슴근", "위팔세갈래근"]
            },
            "intensity": "상",
            "exerciseTime": 20
        }
    ]
}

response = requests.post(url, json=data)
print(response.json())
```

**JavaScript (Fetch)**
```javascript
fetch('https://port-0-exerciesrecord-ai-m09uz3m21c03af28.sel4.cloudtype.app/api/workout-log/analyze', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    date: '2025-10-08',
    memo: '근육을 추가한 후',
    exercises: [
      {
        exercise: {
          title: '팔굽혀펴기',
          muscles: ['어깨세모근', '큰가슴근', '위팔세갈래근']
        },
        intensity: '상',
        exerciseTime: 20
      }
    ]
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

---

### 2. 운동 루틴 추천 요청 예시

**Python**
```python
import requests

url = "https://port-0-exerciesrecord-ai-m09uz3m21c03af28.sel4.cloudtype.app/api/workout-log/recommend"
params = {
    "days": 7,
    "frequency": 4
}

data = {
    "date": "2025-10-08",
    "exercises": [
        {
            "exercise": {
                "title": "팔굽혀펴기",
                "muscles": ["어깨세모근", "큰가슴근"]
            },
            "intensity": "상",
            "exerciseTime": 20
        }
    ]
}

response = requests.post(url, params=params, json=data)
print(response.json())
```

---

## ⚙️ 환경 설정

### 배포 환경 변수

CloudType 배포 시 다음 환경변수를 설정하세요:

```bash
# 필수
PORT=3000
HOST=0.0.0.0
CLOUDTYPE=true
ENVIRONMENT=production

# OpenAI API (AI 기능 사용 시 필수)
OPENAI_API_KEY=sk-your-api-key-here
```

### OpenAI 모델 선택

| 모델 | 속도 | 비용 | 품질 | 권장 용도 |
|------|------|------|------|---------|
| `gpt-4o-mini` | 빠름 | 매우 저렴 | 양호 | 기본 분석 (기본값) |
| `gpt-4o` | 보통 | 저렴 | 우수 | 고급 분석 |
| `gpt-4` | 느림 | 비쌈 | 최고 | 전문 추천 |

---

## 📊 API 문서

### Swagger UI
```
https://port-0-exerciesrecord-ai-m09uz3m21c03af28.sel4.cloudtype.app/docs
```

### ReDoc
```
https://port-0-exerciesrecord-ai-m09uz3m21c03af28.sel4.cloudtype.app/redoc
```

---

## 🔍 테스트 도구

### 로컬 테스트
```bash
python test_deployed_server.py
```

### cURL 예시
```bash
# 헬스 체크
curl https://port-0-exerciesrecord-ai-m09uz3m21c03af28.sel4.cloudtype.app/health

# 운동 목록
curl "https://port-0-exerciesrecord-ai-m09uz3m21c03af28.sel4.cloudtype.app/api/exercises?limit=10"
```

---

## 📌 주요 기능

### ✅ OpenAI 기반 AI 기능
- 운동 일지 자연어 분석
- 맞춤 운동 루틴 생성
- 개인화된 운동 조언

### ✅ 기본 분석 기능
- 운동 통계 (개수, 시간, 강도)
- 신체 부위별 분석
- 추천 및 경고 메시지

### ✅ 운동 데이터베이스
- 20개 이상의 운동 정보
- 부위/난이도/목표별 필터링
- 검색 기능

### ✅ 외부 API 연동
- 한국스포츠개발원 운동 영상 API
- 실시간 영상 검색

---

## 🆘 문제 해결

### OpenAI API 오류
```
오류: "OpenAI API 키가 설정되지 않았습니다."
해결: CloudType 환경변수에 OPENAI_API_KEY 추가
```

### 타임아웃 오류
```
해결: OpenAI API 호출 시 timeout=30 설정 권장
```

### CORS 오류
```
현재 설정: allow_origins=["*"]
배포 환경에서 추가 설정 필요시 알려주세요
```

---

## 📞 지원

API 관련 문의 및 버그 리포트:
- GitHub: https://github.com/Team2Kim/exerciesRecord-AI
- 이슈: https://github.com/Team2Kim/exerciesRecord-AI/issues

---

**버전**: 1.0.0  
**최종 업데이트**: 2025-10-26  
**Base URL**: `https://port-0-exerciesrecord-ai-m09uz3m21c03af28.sel4.cloudtype.app`


