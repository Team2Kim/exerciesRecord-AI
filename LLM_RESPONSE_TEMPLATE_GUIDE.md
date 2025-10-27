# LLM 응답 형식 고정하기

## 개요

LLM의 응답 형식을 일관되게 유지하기 위해 **JSON 형식**을 사용하도록 설정했습니다.

## 주요 변경사항

### 1. `response_format` 파라미터 추가

```python
response = self.client.chat.completions.create(
    model=model,
    messages=[...],
    response_format={"type": "json_object"}  # JSON 형식 강제
)
```

이 파라미터를 추가하면 LLM이 반드시 JSON 형식으로만 응답합니다.

### 2. System Message에 JSON 스키마 명시

각 메서드의 system message에 정확한 JSON 구조를 명시했습니다:

#### 운동 분석 (`analyze_workout_log`)

```json
{
    "workout_evaluation": "운동 강도와 시간에 대한 평가 내용",
    "target_muscles": "타겟 근육과 효과 분석 내용",
    "recommendations": {
        "next_workout": "다음 운동 추천",
        "improvements": "개선 포인트",
        "precautions": "주의사항"
    },
    "encouragement": "격려 메시지"
}
```

#### 운동 루틴 추천 (`recommend_workout_routine`)

```json
{
    "workout_goal": "운동 목표와 방향성",
    "weekly_overview": {
        "day_1": "첫째 날 운동 부위와 포인트",
        "day_2": "둘째 날 운동 부위와 포인트",
        "day_3": "셋째 날 운동 부위와 포인트",
        "day_4": "넷째 날 운동 부위와 포인트"
    },
    "daily_routines": [
        {
            "day": 1,
            "target_body_parts": ["부위1", "부위2"],
            "exercises": [
                {
                    "name": "운동명",
                    "sets": "세트 수",
                    "reps": "반복 횟수",
                    "rest": "휴식 시간",
                    "notes": "포인트"
                }
            ],
            "total_duration": "예상 시간"
        }
    ],
    "tips_and_precautions": "주의사항과 팁"
}
```

#### 종합 분석 (`generate_workout_recommendation`)

```json
{
    "pattern_analysis": {
        "strengths": "현재 운동 패턴의 장점",
        "weaknesses": "개선이 필요한 부분"
    },
    "recommendations": {
        "focus_areas": ["개선 포인트1", "개선 포인트2"],
        "workout_routine": "추천 운동 루틴 설명",
        "tips": "주의사항 및 부상 예방 팁"
    },
    "encouragement": "격려 메시지"
}
```

### 3. JSON 파싱 추가

응답을 자동으로 파싱하여 구조화된 데이터로 반환합니다:

```python
# JSON 응답 파싱
try:
    parsed_analysis = json.loads(ai_analysis)
except json.JSONDecodeError:
    # JSON 파싱 실패 시 원본 문자열 반환
    parsed_analysis = {"raw_response": ai_analysis}
```

## 사용 방법

### 기본 사용

```python
from services.openai_service import openai_service

# 운동 분석
result = openai_service.analyze_workout_log(workout_log)
print(result["analysis"]["workout_evaluation"])
print(result["analysis"]["recommendations"]["next_workout"])

# 운동 루틴 추천
routine = openai_service.recommend_workout_routine(workout_log, days=7, frequency=4)
print(routine["routine"]["workout_goal"])
print(routine["routine"]["daily_routines"][0]["exercises"])

# 종합 분석
recommendation = openai_service.generate_workout_recommendation(analysis_data)
print(recommendation["ai_recommendation"]["pattern_analysis"]["strengths"])
```

## 템플릿을 커스터마이징하는 방법

### 1. System Message 수정

`services/openai_service.py` 파일에서 각 메서드의 system message를 수정하세요:

```python
content = """당신은 전문 운동 코치입니다. 반드시 다음 JSON 형식으로만 응답하세요:

{
    "your_custom_field": "값",
    "another_field": {
        "nested": "값"
    }
}

위 JSON 구조를 따르세요."""
```

### 2. 더 엄격한 스키마 사용 (고급)

OpenAI의 최신 모델들은 더 상세한 JSON 스키마를 지원합니다:

```python
response = self.client.chat.completions.create(
    model=model,
    messages=[...],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "workout_analysis",
            "schema": {
                "type": "object",
                "properties": {
                    "workout_evaluation": {
                        "type": "string",
                        "description": "운동 평가"
                    },
                    "recommendations": {
                        "type": "object",
                        "properties": {
                            "next_workout": {"type": "string"}
                        }
                    }
                },
                "required": ["workout_evaluation", "recommendations"]
            }
        }
    }
)
```

## 장점

1. **일관된 응답 형식**: 매번 같은 구조의 JSON 응답
2. **파싱 용이성**: 자동으로 구조화된 데이터 처리
3. **에러 방지**: JSON 파싱 실패 시 fallback 처리
4. **유지보수 용이**: 명확한 스키마로 코드 이해가 쉬움

## 주의사항

1. `response_format`은 `gpt-4` 이상 모델에서 제대로 작동합니다.
2. JSON 파싱 실패 시 원본 문자열을 반환하도록 처리했습니다.
3. System message에 명시된 스키마를 정확히 따라야 합니다.

## 테스트

```bash
python test_openai_analysis.py
```

## 참고 자료

- [OpenAI Response Format 문서](https://platform.openai.com/docs/api-reference/chat/create#chat-create-response_format)
- [JSON Schema 규격](https://json-schema.org/)
