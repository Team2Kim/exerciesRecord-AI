# 🏋️ ExRecAI - 운동 추천 AI 시스템

## 📋 프로젝트 개요

사용자의 운동 목표와 선호하는 루틴을 바탕으로 개인화된 운동을 추천하는 AI 시스템입니다.

### 🎯 주요 기능

- **개인 맞춤 운동 추천**: 사용자의 목표(근육 증가, 다이어트, 체력 향상)에 맞는 운동 추천
- **루틴 기반 분할**: 주간 빈도(3회, 4회, 5회)와 분할 방식(2분할, 3분할, 전신)에 따른 운동 계획  
- **운동 데이터베이스**: 체계적으로 분류된 운동 정보 관리
- **실시간 추천**: FastAPI를 통한 빠른 응답 시간
- **🎬 운동 영상 통합**: 외부 API 연동으로 실제 운동 영상 제공
- **🔍 영상 검색**: 키워드, 부위, 도구별 운동 영상 검색
- **🤖 향상된 AI 추천**: 영상 정보가 포함된 개인화 추천

### 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   Database      │
│   (Web UI)      │───▶│   Backend       │───▶│   (SQLite)      │
│                 │    │                 │    │                 │
│ - 사용자 입력    │    │ - 추천 로직      │    │ - 운동 데이터    │
│ - 결과 표시      │    │ - API 엔드포인트 │    │ - 사용자 정보    │
│ - 영상 검색      │    │ - 외부 API 연동  │    │ - 피드백 데이터   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        
                                ▼                        
                       ┌─────────────────┐               
                       │  External API   │               
                       │ (운동 영상 DB)   │               
                       │                 │               
                       │ - 영상 검색      │               
                       │ - 근육별 분류    │               
                       │ - 인기 영상      │               
                       └─────────────────┘               
```

### 🛠️ 기술 스택

#### Backend
- **FastAPI**: 고성능 웹 프레임워크
- **SQLAlchemy**: ORM (Object-Relational Mapping)
- **SQLite**: 경량 데이터베이스 (개발용)
- **Pydantic**: 데이터 검증 및 모델링
- **httpx**: 비동기 HTTP 클라이언트 (외부 API 통신)

#### AI/ML
- **scikit-learn**: 머신러닝 알고리즘 (추후 확장)
- **pandas**: 데이터 처리
- **numpy**: 수치 계산

#### Frontend
- **HTML/CSS/JavaScript**: 기본 웹 인터페이스
- **Bootstrap**: UI 프레임워크

### 📊 데이터 모델

#### 운동 정보 (Exercise)
```sql
- id: 운동 고유 ID
- name: 운동 명칭
- body_part: 주요 운동 부위 (가슴, 등, 하체, 어깨, 팔, 코어)
- category: 운동 유형 (웨이트, 체중, 유산소, 스트레칭)
- difficulty: 난이도 (초급, 중급, 고급)
- duration: 예상 소요 시간 (분)
- equipment: 필요 장비
- target_goal: 목표 유형 (근육 증가, 다이어트, 체력 향상)
```

#### 사용자 목표 (UserGoal)
```sql
- user_id: 사용자 ID
- weekly_frequency: 주간 운동 빈도
- split_type: 분할 방식
- primary_goal: 주 목표
- experience_level: 경험 수준
- available_time: 1회 운동 가능 시간
```

### 🔄 추천 알고리즘

#### 1단계: 규칙 기반 필터링
- 분할 방식에 따른 운동 부위 분류
- 사용자 목표에 맞는 운동 유형 선별
- 경험 수준에 따른 난이도 조정

#### 2단계: 스코어링 및 랭킹
- 목표 일치도 (40%)
- 부위별 균형도 (30%)
- 시간 효율성 (20%)
- 다양성 (10%)

#### 3단계: 개인화 (추후 확장)
- 사용자 피드백 학습
- 협업 필터링
- 성과 기반 조정

### 🚀 시작하기

#### 1. 환경 설정
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

#### 2. 데이터베이스 초기화
```bash
python init_database.py
```

#### 3. 서버 실행
```bash
python main.py
```

#### 4. 웹 인터페이스 접속
```
http://localhost:8000
```

### 📁 프로젝트 구조

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
├── models/
│   ├── __init__.py
│   ├── database.py            # 데이터베이스 모델
│   └── schemas.py             # Pydantic 스키마
├── services/
│   ├── __init__.py
│   ├── recommendation.py      # AI 추천 로직
│   ├── database_service.py    # DB 서비스
│   └── external_api.py        # 외부 API 연동 서비스
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

### 🎮 사용 예시

#### 기본 운동 추천 API
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

#### 향상된 추천 API (영상 포함)
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

#### 영상 검색 API
```http
GET /api/videos/search?keyword=벤치프레스&target_group=성인&size=10
```

#### API 응답
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

### 🔮 향후 계획

#### Phase 1 (완료) ✅
- [x] 기본 웹 API 구현
- [x] 규칙 기반 추천 시스템
- [x] 웹 인터페이스
- [x] 외부 운동 영상 API 통합
- [x] 향상된 AI 추천 (영상 포함)

#### Phase 2 (1-2개월)
- [x] 사용자 피드백 시스템 ✅
- [ ] 머신러닝 모델 통합
- [ ] 운동 기록 추적
- [ ] AI 영상 분석 (자세 교정)

#### Phase 3 (3-4개월)
- [ ] 모바일 앱 (React Native)
- [ ] 소셜 기능 (운동 친구, 챌린지)
- [ ] 개인 트레이너 연결
- [ ] 웨어러블 디바이스 연동

### 📞 문의사항

프로젝트 관련 질문이나 개선 제안이 있으시면 언제든 연락주세요!

---
**ExRecAI** - AI로 더 스마트한 운동을! 💪
#   e x e r c i e s R e c o r d - A I  
 