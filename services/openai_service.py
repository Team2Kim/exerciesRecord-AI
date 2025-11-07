"""
OpenAI API 서비스
파인튜닝된 LLM을 활용한 운동 관련 AI 서비스
"""

from openai import OpenAI
import os
import json
from typing import Optional, Dict, Any, List
from models.schemas import ComprehensiveAnalysis
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 근육 라벨(권장 표준 명칭) 리스트
# 모델 프롬프트에서 이 리스트 내의 명칭만 사용하도록 강제합니다
MUSCLE_LABELS: List[str] = [
    "가로돌기사이근","가시사이근","가시아래근","가시윗근","가자미근","가쪽넓은근","궁둥구멍근","긴모음근","긴목근","긴발가락폄근",
    "긴엄지발가락폄근","넓은등근","넙다리곧은근","넙다리근막긴장근","넙다리네갈래근","넙다리두갈래근","넙다리빗근","노쪽 손목 폄근",
    "노쪽손목굽힘근","돌림근","두덩정강근","뒤넙다리근","뒤세모근","뒤정강근","등가시근","등세모근","마름모근","머리가장긴근",
    "머리널판근","머리반가시근","모음근","목/머리널판근","목빗근","뭇갈래근","바깥갈비사이근","반막모양근","반힘줄모양근","배가로근",
    "배곧은근","배바깥빗근","배빗근","배속빗근","볼기근","손목굽힘근","손목폄근","안쪽갈비사이근","안쪽넓은근","앞세모근","앞정강근",
    "앞톱니근","어깨밑근","어깨세모근","어깨올림근","엉덩관절굽힘근","엉덩근","엉덩허리근","위팔근","위팔노근","위팔두갈래근",
    "위팔세갈래근","작은가슴근","작은볼기근","작은원근","장딴지근","장딴지세갈래근","중간볼기근","중간어깨세모근","짧은 모음근",
    "척추세움근","큰가슴근","큰볼기근","큰원근","큰허리근","허리근","허리네모근","허리엉덩갈비근"
]

# 일반적인 근육 이름을 정확한 MUSCLE_LABELS로 매핑하는 딕셔너리
MUSCLE_NAME_MAPPING: Dict[str, List[str]] = {
    # 어깨 관련
    "어깨근육": ["어깨세모근", "어깨올림근", "어깨밑근", "중간어깨세모근"],
    "어깨": ["어깨세모근", "어깨올림근", "어깨밑근"],
    
    # 팔 관련
    "팔근육": ["위팔두갈래근", "위팔세갈래근", "위팔근", "위팔노근"],
    "팔": ["위팔두갈래근", "위팔세갈래근", "위팔근"],
    "삼두": ["위팔세갈래근"],
    "이두": ["위팔두갈래근"],
    
    # 복근 관련
    "복근": ["배곧은근", "배가로근", "배바깥빗근", "배속빗근"],
    "복부": ["배곧은근", "배가로근"],
    "코어": ["배곧은근", "배가로근", "허리근"],
    
    # 종아리 관련
    "종아리근육": ["장딴지근", "장딴지세갈래근", "뒤정강근"],
    "종아리": ["장딴지근", "장딴지세갈래근"],
    
    # 가슴 관련
    "가슴": ["큰가슴근", "작은가슴근"],
    
    # 등 관련
    "등": ["넓은등근", "등세모근", "등가시근"],
    
    # 하체 관련
    "하체": ["넙다리네갈래근", "넙다리두갈래근", "뒤넙다리근", "큰볼기근", "중간볼기근", "작은볼기근"],
    "허벅지": ["넙다리네갈래근", "넙다리두갈래근", "뒤넙다리근"],
    "대퇴": ["넙다리네갈래근", "넙다리두갈래근"],
    
    # 허리 관련
    "허리": ["큰허리근", "허리근", "허리네모근"],
}


def validate_and_map_muscles(muscle_names: List[str]) -> List[str]:
    """
    근육 이름 목록을 검증하고 MUSCLE_LABELS에 맞게 매핑합니다.
    
    Args:
        muscle_names: 검증할 근육 이름 목록
        
    Returns:
        MUSCLE_LABELS에 포함된 유효한 근육 이름 목록
    """
    validated_muscles = []
    
    for muscle in muscle_names:
        muscle = muscle.strip()
        
        # 이미 MUSCLE_LABELS에 있으면 그대로 사용
        if muscle in MUSCLE_LABELS:
            validated_muscles.append(muscle)
            continue
        
        # 매핑 딕셔너리에서 찾기
        if muscle in MUSCLE_NAME_MAPPING:
            # 매핑된 근육 중 첫 번째 것을 사용 (또는 모두 추가 가능)
            mapped = MUSCLE_NAME_MAPPING[muscle]
            validated_muscles.extend(mapped[:1])  # 첫 번째 매핑만 사용
            continue
        
        # 부분 매칭으로 찾기 (예: "어깨"가 포함된 경우)
        found = False
        for label in MUSCLE_LABELS:
            if muscle in label or label in muscle:
                validated_muscles.append(label)
                found = True
                break
        
        # 매핑되지 않으면 무시 (로그는 남기지 않음)
        if not found:
            # 유사한 근육 찾기 (키워드 기반)
            muscle_lower = muscle.lower()
            for key, mapped_list in MUSCLE_NAME_MAPPING.items():
                if key in muscle_lower or muscle_lower in key:
                    validated_muscles.extend(mapped_list[:1])
                    found = True
                    break
    
    # 중복 제거 및 순서 유지
    seen = set()
    result = []
    for muscle in validated_muscles:
        if muscle not in seen:
            seen.add(muscle)
            result.append(muscle)
    
    return result


class OpenAIService:
    """OpenAI API 서비스"""
    
    def __init__(self):
        # API 키는 환경변수에서 로드하는 것이 안전합니다
        api_key = os.getenv("OPENAI_API_KEY", "")
        self.client = OpenAI(api_key=api_key) if api_key else None
        
    def generate_workout_recommendation(
        self, 
        analysis_data: ComprehensiveAnalysis,
        user_preferences: Optional[Dict[str, Any]] = None,
        model: str = "gpt-4o-mini"
    ) -> Dict[str, Any]:
        """
        운동 일지 분석 결과를 기반으로 AI 추천을 생성합니다.
        
        Args:
            analysis_data: 종합 분석 결과
            user_preferences: 사용자 선호도 (선택적)
            model: 사용할 OpenAI 모델 (기본값: "gpt-4o-mini")
            
        Returns:
            Dict[str, Any]: AI 추천 결과
        """
        
        if not self.client:
            return {
                "success": False,
                "message": "OpenAI API 키가 설정되지 않았습니다.",
                "fallback_recommendations": analysis_data.insights.recommendations
            }
        
        try:
            # 분석 결과를 프롬프트로 변환
            prompt = self._create_workout_analysis_prompt(analysis_data)
            
            # OpenAI API 호출 - 고정된 JSON 형식
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": """당신은 전문 운동 코치입니다. 반드시 다음 JSON 형식으로만 응답하세요:

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
    "next_target_muscles": ["근육명1", "근육명2"]
    "encouragement": "격려 메시지"
}

한국어로 친근하고 격려하는 톤을 유지하면서 반드시 위 JSON 구조를 따르세요.

⚠️ 중요: next_target_muscles 필드는 반드시 아래 근육 라벨 목록에 정확히 포함된 이름만 사용해야 합니다.
다른 이름(예: "어깨근육", "팔근육", "복근", "종아리근육" 등)은 절대 사용하지 마세요.
반드시 아래 목록에서 정확한 근육명을 선택하세요."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1000,
                response_format={"type": "json_object"}  # JSON 형식 고정
            )
            
            ai_recommendation = response.choices[0].message.content
            
            # JSON 응답 파싱
            try:
                parsed_recommendation = json.loads(ai_recommendation)
                
                # next_target_muscles 검증 및 매핑
                if "next_target_muscles" in parsed_recommendation:
                    original_muscles = parsed_recommendation["next_target_muscles"]
                    if isinstance(original_muscles, list):
                        validated_muscles = validate_and_map_muscles(original_muscles)
                        parsed_recommendation["next_target_muscles"] = validated_muscles
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 원본 문자열 반환
                parsed_recommendation = {"raw_response": ai_recommendation}
            
            return {
                "success": True,
                "ai_recommendation": parsed_recommendation,  # 파싱된 JSON 반환
                "original_insights": {
                    "overworked_parts": analysis_data.insights.overworked_parts,
                    "underworked_parts": analysis_data.insights.underworked_parts,
                    "balance_score": analysis_data.insights.balance_score
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"AI 분석 중 오류 발생: {str(e)}",
                "fallback_recommendations": analysis_data.insights.recommendations
            }
    
    def analyze_workout_log(self, workout_log: Dict[str, Any], model: str = "gpt-4o-mini") -> Dict[str, Any]:
        """
        운동 일지 데이터를 분석하고 평가합니다.
        
        Args:
            workout_log: 외부 API에서 받은 운동 일지 데이터
            model: 사용할 OpenAI 모델 (기본값: "gpt-4o-mini")
            
        Returns:
            Dict[str, Any]: AI 분석 결과
        """
        
        if not self.client:
            return {
                "success": False,
                "message": "OpenAI API 키가 설정되지 않았습니다."
            }
        
        try:
            # 로그 데이터를 프롬프트로 변환
            prompt = self._create_log_analysis_prompt(workout_log)
            
            # OpenAI API 호출 - 고정된 형식 사용
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": """당신은 전문 운동 코치입니다. 반드시 다음 JSON 형식으로만 응답하세요:

{
    "workout_evaluation": "운동 강도와 시간에 대한 평가 내용",
    "target_muscles": "타겟 근육과 효과 분석 내용",
    "recommendations": {
        "next_workout": "다음 운동 추천",
        "improvements": "개선 포인트",
        "precautions": "주의사항"
    },
    "next_target_muscles": ["근육명1", "근육명2", "근육명3"],
    "encouragement": "격려 메시지"
}

친근하고 격려하는 톤을 유지하면서 반드시 위 JSON 구조를 따르세요.

next_workout에서 추천하는 훈련과 next_target_muscles에 포함된 근육은 일치해야 합니다.
예를 들어 next_workout에서 다음 훈련으로 하체를 추천한다면 next_target_muscles에는 하체 근육이 포함되어야 합니다.

⚠️ 중요: next_target_muscles 필드는 반드시 아래 근육 라벨 목록에 정확히 포함된 이름만 사용해야 합니다.
다른 이름(예: "어깨근육", "팔근육", "복근", "종아리근육" 등)은 절대 사용하지 마세요.
반드시 아래 목록에서 정확한 근육명을 선택하세요."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,
                max_tokens=1500,
                response_format={"type": "json_object"}  # JSON 형식 고정
            )
            
            ai_analysis = response.choices[0].message.content
            
            # JSON 응답 파싱
            try:
                parsed_analysis = json.loads(ai_analysis)
                
                # next_target_muscles 검증 및 매핑
                if "next_target_muscles" in parsed_analysis:
                    original_muscles = parsed_analysis["next_target_muscles"]
                    if isinstance(original_muscles, list):
                        validated_muscles = validate_and_map_muscles(original_muscles)
                        parsed_analysis["next_target_muscles"] = validated_muscles
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 원본 문자열 반환
                parsed_analysis = {"raw_response": ai_analysis}
            
            return {
                "success": True,
                "analysis": parsed_analysis,  # 파싱된 JSON 반환
                "model": model
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"AI 분석 중 오류 발생: {str(e)}"
            }
    
    def recommend_workout_routine(
        self, 
        workout_log: Dict[str, Any],
        days: int = 7,
        frequency: int = 4,
        model: str = "gpt-4o-mini"
    ) -> Dict[str, Any]:
        """
        운동 일지를 기반으로 맞춤 운동 루틴을 추천합니다.
        
        Args:
            workout_log: 외부 API에서 받은 운동 일지 데이터
            days: 다음 며칠간의 루틴 (기본 7일)
            frequency: 주간 운동 빈도
            model: 사용할 OpenAI 모델 (기본값: "gpt-4o-mini")
            
        Returns:
            Dict[str, Any]: AI 추천 루틴
        """
        
        if not self.client:
            return {
                "success": False,
                "message": "OpenAI API 키가 설정되지 않았습니다."
            }
        
        try:
            # 루틴 추천 프롬프트 생성
            prompt = self._create_routine_recommendation_prompt(workout_log, days, frequency)
            
            # OpenAI API 호출 - 고정된 JSON 형식
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": f"""당신은 전문 운동 코치입니다. 반드시 다음 JSON 형식으로만 응답하세요:

{{
    "workout_goal": "운동 목표와 방향성",
    "weekly_overview": {{
        "day_1": "첫째 날 운동 부위와 포인트",
        "day_2": "둘째 날 운동 부위와 포인트",
        "day_3": "셋째 날 운동 부위와 포인트",
        "day_4": "넷째 날 운동 부위와 포인트"
    }},
    "daily_routines": [
        {{
            "day": 1,
            "target_body_parts": ["부위1", "부위2"],
            "exercises": [
                {{
                    "name": "운동명",
                    "sets": "세트 수",
                    "reps": "반복 횟수",
                    "rest": "휴식 시간",
                    "notes": "포인트"
                }}
            ],
            "total_duration": "예상 시간"
        }}
    ],
    "tips_and_precautions": "주의사항과 팁",
    "next_target_muscles": ["근육명1", "근육명2", "근육명3"]

구체적이고 실천 가능한 내용을 위 구조로 제시하세요.
주의: next_target_muscles는 반드시 제공된 근육 라벨 목록에서만 선택하세요."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}  # JSON 형식 고정
            )
            
            ai_routine = response.choices[0].message.content
            
            # JSON 응답 파싱
            try:
                parsed_routine = json.loads(ai_routine)
                
                # next_target_muscles 검증 및 매핑
                if "next_target_muscles" in parsed_routine:
                    original_muscles = parsed_routine["next_target_muscles"]
                    if isinstance(original_muscles, list):
                        validated_muscles = validate_and_map_muscles(original_muscles)
                        parsed_routine["next_target_muscles"] = validated_muscles
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 원본 문자열 반환
                parsed_routine = {"raw_response": ai_routine}
            
            return {
                "success": True,
                "routine": parsed_routine,  # 파싱된 JSON 반환
                "days": days,
                "frequency": frequency,
                "model": model
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"루틴 추천 중 오류 발생: {str(e)}"
            }

    def analyze_weekly_pattern_and_recommend(
        self,
        weekly_logs: List[Dict[str, Any]],
        model: str = "gpt-4o-mini"
    ) -> Dict[str, Any]:
        """
        7일치 운동 데이터를 기반으로 패턴을 분석하고 맞춤 루틴을 추천합니다.

        Args:
            weekly_logs: 날짜 역순 또는 순차 정렬된 7일치 운동 기록 리스트
            model: 사용할 OpenAI 모델 (기본값: "gpt-4o-mini")

        Returns:
            Dict[str, Any]: 패턴 분석 및 루틴 추천 결과
        """

        if not self.client:
            return {
                "success": False,
                "message": "OpenAI API 키가 설정되지 않았습니다."
            }

        try:
            prompt = self._create_weekly_pattern_prompt(weekly_logs)

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": f"""당신은 전문 운동 코치이자 데이터 분석가입니다. 반드시 다음 JSON 형식으로만 응답하세요:

{{
    "pattern_analysis": {{
        "consistency": "훈련 빈도와 규칙성 분석",
        "intensity_trend": "강도 변화와 피로 누적에 대한 평가",
        "muscle_balance": {{
            "overworked": ["근육명1", "근육명2"],
            "underworked": ["근육명3", "근육명4"],
            "comments": "근육 사용 균형에 대한 종합 의견"
        }},
        "habit_observation": "생활 패턴 및 회복 습관 관련 인사이트"
    }},
    "recommended_routine": {{
        "weekly_overview": [
            "요일별 주요 타겟과 목표",
            "필요 시 휴식/회복 권장"
        ],
        "daily_details": [
            {{
                "day": 1,
                "focus": "주요 부위 및 목표",
                "exercises": [
                    {{
                        "name": "운동명",
                        "sets": "세트 수",
                        "reps": "반복 수",
                        "rest": "휴식 시간",
                        "notes": "폼 또는 강도 조절 팁"
                    }}
                ],
                "estimated_duration": "예상 소요 시간"
            }}
        ],
        "progression_strategy": "점진적 과부하 또는 변화를 위한 전략"
    }},
    "recovery_guidance": "영양, 수면, 스트레칭 등 회복 팁",
    "next_target_muscles": ["근육명1", "근육명2", "근육명3"],
    "encouragement": "격려 메시지"
}}

친근하고 격려하는 톤을 유지하면서 반드시 위 JSON 구조를 따르세요.

⚠️ 중요: next_target_muscles, muscle_balance.overworked, muscle_balance.underworked 필드는 반드시 아래 근육 라벨 목록에 정확히 포함된 이름만 사용해야 합니다.
다른 이름(예: "어깨근육", "팔근육", "복근" 등)은 절대 사용하지 마세요.
반드시 아래 목록에서 정확한 근육명을 선택하세요."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2200,
                response_format={"type": "json_object"}
            )

            ai_response = response.choices[0].message.content

            try:
                parsed_response = json.loads(ai_response)

                for key in [
                    ("next_target_muscles", parsed_response.get("next_target_muscles")),
                    ("overworked", parsed_response.get("pattern_analysis", {})
                                 .get("muscle_balance", {})
                                 .get("overworked")),
                    ("underworked", parsed_response.get("pattern_analysis", {})
                                 .get("muscle_balance", {})
                                 .get("underworked"))
                ]:
                    field_name, muscles = key
                    if isinstance(muscles, list):
                        validated = validate_and_map_muscles(muscles)

                        if field_name == "next_target_muscles":
                            parsed_response["next_target_muscles"] = validated
                        else:
                            muscle_balance = parsed_response.setdefault("pattern_analysis", {}).setdefault("muscle_balance", {})
                            muscle_balance[field_name] = validated
            except json.JSONDecodeError:
                parsed_response = {"raw_response": ai_response}

            return {
                "success": True,
                "result": parsed_response,
                "model": model
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"주간 패턴 분석 중 오류 발생: {str(e)}"
            }
    
    def _create_log_analysis_prompt(self, workout_log: Dict[str, Any]) -> str:
        """운동 일지 데이터를 프롬프트로 변환"""
        
        date = workout_log.get("date", "날짜 정보 없음")
        memo = workout_log.get("memo", "")
        exercises = workout_log.get("exercises", [])
        
        prompt = f"""
사용자의 운동 일지를 분석해주세요.

[운동 일지 정보]
날짜: {date}
메모: {memo}

[운동 상세]
"""
        
        for i, ex_data in enumerate(exercises, 1):
            exercise = ex_data.get("exercise", {})
            prompt += f"""
운동 {i}:
- 운동명: {exercise.get('title', 'N/A')}
- 근육 부위: {', '.join(exercise.get('muscles', []))}
- 강도: {ex_data.get('intensity', 'N/A')}
- 운동 시간: {ex_data.get('exerciseTime', 0)}분
- 운동 도구: {exercise.get('exerciseTool', 'N/A')}
"""
        
        prompt += """

위 운동 일지를 분석하여 다음을 포함한 상세 평가를 작성해주세요:
1. 전반적인 운동 평가 (강도, 시간, 다양한성)
2. 타겟 근육 분석 및 효과
3. 좋은 점과 개선할 점
4. 다음 운동을 위한 구체적인 추천
5. 부상 예방을 위한 주의사항

[근육 라벨 목록]
아래 목록에 포함된 근육명만 사용하여 다음 운동을 추천할 근육(next_target_muscles)을 2~5개 선정하세요.
선정 기준: (1) 최근 기록에서 부족하거나 덜 사용된 근육, (2) 과사용 부위는 피함, (3) 전신 균형 개선.
{', '.join(MUSCLE_LABELS)}

친근하고 격려하는 톤으로 작성해주세요."""
        
        return prompt
    
    def _create_routine_recommendation_prompt(
        self, 
        workout_log: Dict[str, Any], 
        days: int, 
        frequency: int
    ) -> str:
        """운동 루틴 추천을 위한 프롬프트 생성"""
        
        date = workout_log.get("date", "날짜 정보 없음")
        exercises = workout_log.get("exercises", [])
        
        # 근육 그룹 추출
        muscle_groups = []
        for ex_data in exercises:
            exercise = ex_data.get("exercise", {})
            muscles = exercise.get("muscles", [])
            muscle_groups.extend(muscles)
        
        unique_muscles = list(set(muscle_groups))
        
        prompt = f"""
사용자의 최근 운동 기록:
날짜: {date}

주요 근육 그룹:
{', '.join(unique_muscles) if unique_muscles else '기록 없음'}

주 {frequency}회, {days}일간의 운동 루틴을 작성해주세요.

사용자의 운동 수준과 패턴을 고려하여:
- 전신 균형을 고려한 분할 방식
- 적절한 운동 강도와 빈도
- 점진적 과부하 원칙
- 안전하고 실천 가능한 루틴

상세한 운동명, 세트, 횟수, 휴식시간까지 포함해주세요.

[근육 라벨 목록]
아래 목록에 포함된 근육명만 사용하여 다음 운동을 추천할 근육(next_target_muscles)을 2~5개 선정하세요.
선정 기준: (1) 최근 기록에서 부족하거나 덜 사용된 근육, (2) 과사용 부위는 피함, (3) 전신 균형 개선.
{', '.join(MUSCLE_LABELS)}"""
        
        return prompt
    
    def _create_workout_analysis_prompt(self, analysis: ComprehensiveAnalysis) -> str:
        """분석 결과를 프롬프트로 변환"""
        
        pattern = analysis.pattern
        
        prompt = f"""
사용자의 운동 일지 분석 결과입니다. 이 데이터를 바탕으로 맞춤형 조언을 제공해주세요.

[운동 통계]
- 분석 기간: {analysis.analysis_period}
- 총 운동 횟수: {pattern.total_workouts}일
- 총 운동 개수: {pattern.total_exercises}개
- 총 운동 시간: {pattern.total_time}분
- 평균 운동 시간: {pattern.avg_workout_time}분/일

[신체 부위별 비율]
"""
        
        for bp in pattern.body_part_distribution:
            prompt += f"- {bp.body_part}: {bp.percentage}% ({bp.exercise_count}회)\n"
        
        prompt += f"""
[가장 많이 한 운동]
"""
        for exercise in pattern.most_frequent_exercises[:5]:
            prompt += f"- {exercise['name']}: {exercise['count']}회 ({exercise['body_part']})\n"
        
        prompt += f"""
[운동 강도]
- 상강도: {pattern.intensity_distribution['상']}개
- 중강도: {pattern.intensity_distribution['중']}개
- 하강도: {pattern.intensity_distribution['하']}개

[현재 문제점]
- 과사용 부위: {', '.join(analysis.insights.overworked_parts) if analysis.insights.overworked_parts else '없음'}
- 부족한 부위: {', '.join(analysis.insights.underworked_parts) if analysis.insights.underworked_parts else '없음'}
- 균형 점수: {analysis.insights.balance_score}/100

위 정보를 바탕으로 다음을 포함한 맞춤형 조언을 제공해주세요:
1. 현재 운동 패턴의 장단점 분석
2. 개선이 필요한 부분과 구체적인 솔루션
3. 추천 운동 루틴
4. 주의사항 및 부상 예방 팁

한국어로 친근하고 격려하는 톤으로 답변해주세요.

[근육 라벨 목록]
아래 목록에 포함된 근육명만 사용하여 다음 운동을 추천할 근육(next_target_muscles)을 2~5개 선정하세요.
선정 기준: (1) 최근 기록에서 부족하거나 덜 사용된 근육, (2) 과사용 부위는 피함, (3) 전신 균형 개선.
{', '.join(MUSCLE_LABELS)}
"""
        return prompt

    def _create_weekly_pattern_prompt(self, weekly_logs: List[Dict[str, Any]]) -> str:
        """7일치 운동 기록을 프롬프트로 변환"""

        if not weekly_logs:
            return "최근 7일간의 운동 기록이 제공되지 않았습니다. 가능한 경우 최근 기록을 기반으로 통찰과 루틴을 제안해주세요."

        prompt = """
사용자의 최근 7일 운동 기록을 분석하고, 패턴을 파악해 적절한 루틴을 제안해주세요.

[7일 운동 기록]
"""

        for idx, log in enumerate(weekly_logs, 1):
            date = log.get("date", "날짜 정보 없음")
            memo = log.get("memo", "")
            exercises = log.get("exercises", [])

            prompt += f"""
날짜 {idx}: {date}
메모: {memo if memo else '메모 없음'}
운동 목록:
"""

            if not exercises:
                prompt += "- 기록된 운동 없음\n"
            else:
                for ex_idx, ex_data in enumerate(exercises, 1):
                    exercise = ex_data.get("exercise", {})
                    prompt += f"- 운동 {ex_idx}: {exercise.get('title', '운동명 없음')} | 사용 근육: {', '.join(exercise.get('muscles', [])) or '정보 없음'} | 강도: {ex_data.get('intensity', '정보 없음')} | 시간: {ex_data.get('exerciseTime', 0)}분 | 도구: {exercise.get('exerciseTool', '정보 없음')}\n"

        prompt += f"""

[분석 및 추천 지침]
1. 주간 운동 빈도, 강도, 회복 상태를 종합 분석
2. 근육 사용량의 불균형, 과사용/부족 부위를 명확히 제시
3. 다음 주를 위한 4~6회 분할 루틴을 구성하고 휴식일 또는 액티브 리커버리 제안 포함
4. 점진적 과부하 전략과 컨디션 조절 팁 포함
5. 회복을 돕는 생활 습관(수면, 영양, 스트레칭) 권장 사항 제시

[근육 라벨 목록]
아래 목록에 포함된 근육명만 사용하여 muscle_balance.overworked, muscle_balance.underworked, next_target_muscles 항목을 구성하세요.
{', '.join(MUSCLE_LABELS)}

친근하고 격려하는 톤으로 작성하되, 실행 가능한 구체적인 정보를 제공해주세요.
"""

        return prompt


# 전역 서비스 인스턴스
openai_service = OpenAIService()
