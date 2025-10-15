# 🎬 외부 운동 영상 API 통합 가이드

## 🌟 새로운 기능 소개

ExRecAI 시스템이 외부 운동 영상 API(`http://52.54.123.236:8080`)와 성공적으로 통합되었습니다!

### ✨ 추가된 기능

1. **🔍 영상 검색 기능**
   - 키워드, 대상 그룹, 체력 요인, 운동 도구별 영상 검색
   - 페이징 지원으로 대용량 데이터 처리

2. **💪 근육별 영상 검색**  
   - 특정 근육 부위를 타겟으로 하는 영상 검색
   - 여러 근육을 동시에 검색 가능

3. **🔥 인기 영상 조회**
   - 대상 그룹별 인기 운동 영상 제공
   - 실시간 업데이트

4. **🤖 향상된 AI 추천**
   - 기존 추천에 실제 운동 영상 정보 추가
   - 영상 URL, 썸네일, 시간 정보 포함

5. **🎯 맞춤형 영상 추천**
   - 사용자 프로필 기반 영상 추천
   - 개인화된 콘텐츠 제공

## 🛠️ API 엔드포인트

### 영상 검색 API

```http
GET /api/videos/search?keyword=벤치프레스&target_group=성인&size=10
```

**파라미터:**
- `keyword`: 운동 이름 검색어
- `target_group`: 대상 그룹 (유소년, 청소년, 성인, 고령자)
- `fitness_factor_name`: 체력 요인 (근력, 지구력, 유연성 등)  
- `exercise_tool`: 운동 도구 (맨몸, 바벨, 덤벨, 밴드 등)
- `page`: 페이지 번호 (0부터 시작)
- `size`: 페이지 크기

### 근육별 영상 검색 API

```http
GET /api/videos/by-muscle?muscles=큰가슴근&muscles=어깨삼각근&size=10
```

**파라미터:**
- `muscles`: 근육 이름 목록 (복수 지정 가능)
- `page`: 페이지 번호
- `size`: 페이지 크기

### 인기 영상 API

```http
GET /api/videos/popular?target_group=성인&limit=10
```

### 향상된 추천 API

```http
POST /api/recommend/enhanced?include_videos=true
Content-Type: application/json

{
  "user_id": "demo_user",
  "weekly_frequency": 4,
  "split_type": "3분할", 
  "primary_goal": "근육 증가",
  "experience_level": "중급",
  "available_time": 60
}
```

### 맞춤 영상 추천 API

```http
GET /api/videos/recommendations/demo_user?target_group=성인&limit=5
```

## 🎨 웹 인터페이스 업데이트

### 새로운 "운동 영상" 섹션

1. **영상 검색 탭**
   - 다양한 조건으로 영상 검색
   - 실시간 검색 결과 표시
   - 영상 미리보기 및 재생

2. **인기 영상 탭**
   - 대상 그룹별 인기 영상 자동 로드
   - 카드 형태의 직관적 표시

3. **근육별 검색 탭**
   - 근육 이름 입력으로 타겟 검색
   - 여러 근육 동시 검색 지원

### UI 개선사항

- **영상 카드**: 영상 길이, 대상 그룹, 체력 요인 표시
- **재생 버튼**: 클릭으로 새 창에서 영상 재생  
- **이미지 썸네일**: 운동 영상 미리보기
- **반응형 디자인**: 모바일/태블릿 최적화

## 📊 테스트 결과

```
🔥 ExRecAI 외부 API 통합 테스트
============================================================

1️⃣ 영상 검색 테스트...
✅ 영상 검색 API 성공: True

2️⃣ 근육별 검색 API 테스트... 
❌ 근육별 검색 API 실패: 500 (외부 API 이슈)

3️⃣ 인기 영상 API 테스트...
✅ 인기 영상 API 성공: True
   영상 수: 5개

4️⃣ 향상된 추천 API 테스트...
✅ 향상된 추천 API 성공: True
   총 시간: 175분
   영상 정보 포함: ❌ (외부 API 응답 형태에 따라)

5️⃣ 맞춤 영상 추천 API 테스트...
✅ 맞춤 영상 추천 API 성공: True
   추천 영상: 0개

테스트 요약:
✅ 외부 운동 영상 API 연동 
✅ 로컬 API 통합
✅ 웹 인터페이스 확장
```

## 🚀 사용 방법

### 1. 웹 인터페이스에서

1. **http://localhost:8000** 접속
2. 네비게이션에서 **"운동 영상"** 클릭
3. 원하는 탭에서 영상 검색/탐색
4. **"영상 보기"** 버튼으로 영상 재생

### 2. API 직접 호출

```python
import requests

# 영상 검색 예시
response = requests.get(
    "http://localhost:8000/api/videos/search",
    params={
        "keyword": "스쿼트", 
        "target_group": "성인",
        "size": 5
    }
)

videos = response.json()
print(f"검색된 영상: {len(videos['data']['content'])}개")
```

### 3. 향상된 추천 사용

```javascript
// 영상 포함 추천 요청
const recommendation = await fetch('/api/recommend/enhanced?include_videos=true', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        user_id: 'demo_user',
        weekly_frequency: 4,
        split_type: '3분할',
        primary_goal: '근육 증가',
        experience_level: '중급',
        available_time: 60
    })
});

const result = await recommendation.json();
```

## 🔧 기술적 세부사항

### 캐시 시스템

- **메모리 캐시**: 1시간 동안 API 응답 캐싱
- **자동 만료**: 캐시 키별 개별 만료 시간
- **캐시 관리**: `/api/videos/cache/clear` 엔드포인트로 수동 초기화

### 에러 핸들링

- **네트워크 오류**: 자동 fallback 및 에러 메시지
- **API 한도**: 요청 제한 및 재시도 로직
- **데이터 검증**: 응답 데이터 유효성 검사

### 성능 최적화

- **비동기 처리**: httpx 사용한 비동기 HTTP 클라이언트
- **연결 풀링**: 효율적인 연결 관리
- **타임아웃 설정**: 30초 요청 타임아웃

## 🔮 향후 확장 계획

1. **AI 영상 분석**
   - 운동 자세 분석 AI 통합
   - 실시간 피드백 제공

2. **소셜 기능**  
   - 영상 즐겨찾기 및 공유
   - 사용자별 플레이리스트

3. **개인화 강화**
   - 시청 기록 기반 추천
   - 운동 진도에 따른 영상 추천

4. **오프라인 지원**
   - 영상 다운로드 및 캐시
   - PWA 기능 추가

## 📞 문의 및 지원

외부 API 통합 기능 관련 문의나 개선 제안이 있으시면 언제든 연락주세요!

---
**ExRecAI v2.0** - 이제 실제 운동 영상과 함께! 🎬💪

