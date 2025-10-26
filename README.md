# 🏋️ ExRecAI - 운동 추천 AI 시스템

> **AI로 더 스마트한 운동을!** 💪

사용자의 운동 목표와 선호하는 루틴을 바탕으로 개인화된 운동을 추천하는 AI 시스템입니다.

## 🎯 주요 기능

- **개인 맞춤 운동 추천**: 사용자의 목표(근육 증가, 다이어트, 체력 향상)에 맞는 운동 추천
- **루틴 기반 분할**: 주간 빈도(3회, 4회, 5회)와 분할 방식(2분할, 3분할, 전신)에 따른 운동 계획  
- **운동 데이터베이스**: 체계적으로 분류된 운동 정보 관리
- **실시간 추천**: FastAPI를 통한 빠른 응답 시간
- **🎬 운동 영상 통합**: 외부 API 연동으로 실제 운동 영상 제공
- **🔍 영상 검색**: 키워드, 부위, 도구별 운동 영상 검색
- **🤖 향상된 AI 추천**: 영상 정보가 포함된 개인화 추천

## 🏗️ 시스템 아키텍처

```
Frontend (Web UI) ──→ FastAPI Backend ──→ SQLite Database
                            │
                            └──→ External Video API
```

## 🛠️ 기술 스택

### Backend
- **FastAPI**: 고성능 웹 프레임워크
- **SQLAlchemy**: ORM (Object-Relational Mapping)
- **SQLite**: 경량 데이터베이스 (개발용)
- **Pydantic**: 데이터 검증 및 모델링
- **httpx**: 비동기 HTTP 클라이언트 (외부 API 통신)
- **OpenAI**: GPT-4 기반 AI 운동 분석 및 추천

### AI/ML
- **scikit-learn**: 머신러닝 알고리즘 (추후 확장)
- **pandas**: 데이터 처리
- **numpy**: 수치 계산
- **OpenAI GPT-4**: 자연어 기반 운동 분석 및 추천

### Frontend
- **HTML/CSS/JavaScript**: 기본 웹 인터페이스
- **Bootstrap**: UI 프레임워크

## 📊 데이터 모델

### 운동 정보 (Exercise)
- `id`: 운동 고유 ID
- `name`: 운동 명칭
- `body_part`: 주요 운동 부위 (가슴, 등, 하체, 어깨, 팔, 코어)
- `category`: 운동 유형 (웨이트, 체중, 유산소, 스트레칭)
- `difficulty`: 난이도 (초급, 중급, 고급)
- `duration`: 예상 소요 시간 (분)
- `equipment`: 필요 장비
- `target_goal`: 목표 유형 (근육 증가, 다이어트, 체력 향상)

### 사용자 목표 (UserGoal)
- `user_id`: 사용자 ID
- `weekly_frequency`: 주간 운동 빈도
- `split_type`: 분할 방식
- `primary_goal`: 주 목표
- `experience_level`: 경험 수준
- `available_time`: 1회 운동 가능 시간

## 🧠 추천 알고리즘

### 1단계: 규칙 기반 필터링
- 분할 방식에 따른 운동 부위 분류
- 사용자 목표에 맞는 운동 유형 선별
- 경험 수준에 따른 난이도 조정

### 2단계: 스코어링 및 랭킹
- 목표 일치도 (40%)
- 부위별 균형도 (30%)
- 시간 효율성 (20%)
- 다양성 (10%)

### 3단계: 개인화 (추후 확장)
- 사용자 피드백 학습
- 협업 필터링
- 성과 기반 조정

## 🤖 OpenAI 기반 AI 운동 코치 기능

### 🎯 새로운 기능

**OpenAI GPT 모델을 활용한 지능형 운동 분석 및 루틴 추천:**

1. **운동 일지 AI 분석** (`POST /api/workout-log/analyze`)
   - 운동 강도, 시간, 다양성 평가
   - 타겟 근육 분석 및 효과 평가
   - 다음 운동을 위한 구체적인 추천
   - 부상 예방을 위한 주의사항

2. **AI 운동 루틴 추천** (`POST /api/workout-log/recommend`)
   - 사용자 운동 기록 기반 맞춤 루틴
   - 주간 운동 계획 자동 생성
   - 운동명, 세트, 횟수, 휴식시간 포함
   - 실천 가능한 구체적인 가이드

### 📝 사용 예시

#### 1️⃣ 운동 일지 분석
```json
POST /api/workout-log/analyze
{
  "logId": 3,
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
```

**응답:**
```json
{
  "success": true,
  "ai_analysis": "당신의 운동을 분석한 결과...",
  "basic_analysis": {
    "summary": "2개 운동을 수행했습니다.",
    "recommendations": [...]
  },
  "model": "gpt-4o-mini"
}
```

#### 2️⃣ 운동 루틴 추천
```json
POST /api/workout-log/recommend?days=7&frequency=4
{
  "date": "2025-10-08",
  "exercises": [...]
}
```

**응답:**
```json
{
  "success": true,
  "ai_routine": "다음 7일간의 운동 루틴:\n\nDay 1 (가슴/삼두)...",
  "routine_period": {
    "days": 7,
    "frequency": 4
  },
  "model": "gpt-4o-mini"
}
```

### ⚙️ OpenAI API 설정

`.env` 파일 생성:
```bash
OPENAI_API_KEY=sk-your-api-key-here
```

또는 환경변수로 설정:
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

### 🧪 테스트 방법

```bash
# 테스트 스크립트 실행
python test_openai_analysis.py
```

이 스크립트는 다음을 테스트합니다:
- 운동 일지 AI 분석
- 운동 루틴 추천
- OpenAI API 연동 확인

## 🚀 시작하기

### 1. 환경 설정
```bash
# Python 가상환경 생성
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 데이터베이스 초기화
```bash
python init_database.py
```
이 명령어로 다음 샘플 데이터가 자동 생성됩니다:
- ✅ 20개의 운동 데이터
- ✅ 3개의 사용자 목표
- ✅ 3개의 사용자 피드백
- ✅ **16개의 운동 일지** (최근 30일간 데이터)
- ✅ **64개의 운동 기록** (일지별 3-5개 운동)

샘플 일지는 `demo_user` 계정으로 생성되며, 가슴 운동에 편중된 패턴으로 분석 기능을 바로 테스트할 수 있습니다.

### 3. 서버 실행
```bash
python main.py
```

### 4. 웹 인터페이스 및 API 테스트
```
http://localhost:8000          # 웹 인터페이스
http://localhost:8000/docs     # Swagger UI (API 테스트)
```

## 📁 프로젝트 구조

```
ExRecAI/
├── README.md                    # 프로젝트 개요
├── EXTERNAL_API_INTEGRATION.md  # 외부 API 통합 가이드
├── DEMO_GUIDE.md               # 데모 가이드
├── requirements.txt            # Python 의존성
├── main.py                     # FastAPI 메인 서버
├── init_database.py           # 데이터베이스 초기화
├── test_api.py                # API 테스트 스크립트
├── test_external_api.py       # 외부 API 테스트
├── test_openai_analysis.py    # OpenAI API 테스트
├── models/
│   ├── __init__.py
│   ├── database.py            # 데이터베이스 모델
│   └── schemas.py             # Pydantic 스키마
├── services/
│   ├── __init__.py
│   ├── recommendation.py      # AI 추천 로직
│   ├── database_service.py    # DB 서비스
│   ├── external_api.py        # 외부 API 연동 서비스
│   ├── openai_service.py      # OpenAI AI 서비스
│   └── workout_analysis.py    # 운동 분석 서비스
├── static/
│   ├── css/
│   │   └── style.css          # 커스텀 스타일
│   ├── js/
│   │   ├── app.js             # 메인 JavaScript
│   │   └── video-handlers.js  # 영상 관련 핸들러
│   └── index.html             # 웹 인터페이스
├── data/
│   ├── exercises.json         # 운동 데이터
│   └── fitness.db             # SQLite 데이터베이스
└── tests/
    └── __init__.py
```

## 🎮 사용 예시

### 기본 운동 추천 API
```json
POST /api/recommend
{
  "user_id": "demo_user",
  "weekly_frequency": 4,
  "split_type": "3분할",
  "primary_goal": "근육 증가",
  "experience_level": "중급",
  "available_time": 60
}
```

### 향상된 추천 API (영상 포함)
```json
POST /api/recommend/enhanced?include_videos=true
{
  "user_id": "demo_user",
  "weekly_frequency": 4,
  "split_type": "3분할", 
  "primary_goal": "근육 증가",
  "experience_level": "중급",
  "available_time": 60
}
```

### 영상 검색 API
```http
GET /api/videos/search?keyword=벤치프레스&target_group=성인&size=10
```

### API 응답
```json
{
  "success": true,
  "recommendation": {
    "Day 1 - 가슴/삼두": [
      {
        "name": "벤치프레스",
        "sets": 4,
        "reps": "8-12",
        "rest": "2-3분"
      },
      {
        "name": "인클라인 덤벨프레스",
        "sets": 3,
        "reps": "10-15",
        "rest": "2분"
      }
    ],
    "Day 2 - 등/이두": [...],
    "Day 3 - 하체": [...],
    "Day 4 - 어깨/코어": [...]
  },
  "total_duration": 240,
  "tips": "중급자는 compound 운동을 우선적으로 수행하세요."
}
```

## 📊 운동 일지 분석 기능

### 🧪 샘플 데이터로 바로 테스트하기

데이터베이스 초기화 시 자동으로 생성된 샘플 데이터(`demo_user`)를 사용하여 바로 테스트할 수 있습니다!

#### **웹 브라우저에서 테스트** (추천!)
1. 서버 실행 후 http://localhost:8000/docs 접속
2. `GET /api/analysis/comprehensive/{user_id}` 찾기
3. "Try it out" 클릭
4. `user_id`에 **`demo_user`** 입력
5. "Execute" 클릭하여 결과 확인! 🎉

#### **브라우저 주소창에서 직접 테스트**
```
http://localhost:8000/api/analysis/comprehensive/demo_user?days=30
```

---

### 분석 API 엔드포인트

#### 1. 운동 패턴 분석
```http
GET /api/analysis/workout-pattern/{user_id}?days=30
```

**응답 내용:**
- 총 운동 횟수 및 시간
- 신체 부위별 운동 분포
- 가장 많이 한 운동 목록
- 운동 강도 분포 (상/중/하)

**테스트:**
```
http://localhost:8000/api/analysis/workout-pattern/demo_user?days=30
```

#### 2. 맞춤 인사이트
```http
GET /api/analysis/insights/{user_id}?days=30
```

**응답 내용:**
- 🔴 **과사용 부위**: 휴식이 필요한 신체 부위
- 🟡 **부족한 부위**: 보충 운동이 필요한 부위
- 📈 **균형 점수**: 운동 균형도 (0-100)
- 💡 **추천 사항**: AI 기반 맞춤 추천
- ⚠️ **주의 사항**: 건강을 위한 경고

**테스트:**
```
http://localhost:8000/api/analysis/insights/demo_user?days=30
```

#### 3. 종합 분석 (추천!)
```http
GET /api/analysis/comprehensive/{user_id}?days=30
```

패턴 분석 + 인사이트를 통합한 종합 리포트를 제공합니다.

**테스트:**
```
http://localhost:8000/api/analysis/comprehensive/demo_user?days=30
```

#### 4. AI 기반 맞춤 추천 (OpenAI 연동)
```http
GET /api/analysis/ai-recommendation/{user_id}?days=30
```

**응답 내용:**
- 기본 분석 결과
- AI가 생성한 맞춤형 운동 조언
- 구체적인 추천 운동 루틴

**테스트:**
```
http://localhost:8000/api/analysis/ai-recommendation/demo_user?days=30
```

**설정 방법:**
```bash
# 환경변수에 OpenAI API 키 설정
export OPENAI_API_KEY="your-api-key-here"

# 또는 .env 파일 생성
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

### 📋 예상 분석 결과 (demo_user)

샘플 데이터는 의도적으로 **가슴 운동에 편중**되도록 생성되었습니다:

```json
{
  "user_id": "demo_user",
  "analysis_period": "최근 30일",
  "pattern": {
    "total_workouts": 16,
    "total_exercises": 64,
    "total_time": 1500,
    "body_part_distribution": [
      {"body_part": "가슴", "percentage": 35.0},
      {"body_part": "하체", "percentage": 25.0},
      {"body_part": "어깨", "percentage": 15.0},
      {"body_part": "팔", "percentage": 12.0},
      {"body_part": "등", "percentage": 8.0},
      {"body_part": "코어", "percentage": 5.0}
    ]
  },
  "insights": {
    "overworked_parts": ["가슴"],
    "underworked_parts": ["등", "코어"],
    "balance_score": 65.5,
    "recommendations": [
      "부족한 부위: 등, 코어에 집중하세요.",
      "✅ 양호한 운동 루틴입니다. 조금만 더 균형을 맞춰보세요."
    ],
    "warnings": [
      "과사용 부위: 가슴는 휴식이 필요할 수 있습니다."
    ]
  }
}
```

### 분석 알고리즘
- **신체 부위별 균형 분석**: 가슴, 등, 하체, 어깨, 팔, 코어의 운동 비율 분석
- **과사용 감지**: 특정 부위가 30% 이상 편중된 경우 휴식 권장
- **부족 부위 감지**: 10% 미만인 부위에 대해 보충 운동 추천
- **강도 분석**: 고강도/저강도 운동 비율을 분석하여 적정 수준 제안

## 🔮 향후 계획

### Phase 1 (완료) ✅
- [x] 기본 웹 API 구현
- [x] 규칙 기반 추천 시스템
- [x] 웹 인터페이스
- [x] 외부 운동 영상 API 통합
- [x] 향상된 AI 추천 (영상 포함)
- [x] 운동 일지 분석 시스템 ✅

### Phase 2 (1-2개월)
- [x] 사용자 피드백 시스템 ✅
- [x] 운동 패턴 분석 및 인사이트 ✅
- [x] OpenAI 기반 AI 운동 코치 ✅
- [ ] 머신러닝 모델 통합
- [ ] AI 영상 분석 (자세 교정)

### Phase 3 (3-4개월)
- [ ] 모바일 앱 (React Native)
- [ ] 소셜 기능 (운동 친구, 챌린지)
- [ ] 개인 트레이너 연결
- [ ] 웨어러블 디바이스 연동

## 📞 문의사항

프로젝트 관련 질문이나 개선 제안이 있으시면 언제든 연락주세요!

---
**ExRecAI** - AI로 더 스마트한 운동을! 💪