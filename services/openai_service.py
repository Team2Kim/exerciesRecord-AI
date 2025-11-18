"""
OpenAI API 서비스
파인튜닝된 LLM을 활용한 운동 관련 AI 서비스
"""

from openai import OpenAI
import os
import json
import time
from typing import Optional, Dict, Any, List, Tuple
from models.schemas import ComprehensiveAnalysis
from dotenv import load_dotenv
from services.exercise_rag_service import get_exercise_rag_service, ExerciseRAGService

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
        self.exercise_rag: Optional[ExerciseRAGService] = None
        self.exercise_rag_error: Optional[str] = None

        try:
            self.exercise_rag = get_exercise_rag_service()
        except Exception as exc:
            self.exercise_rag_error = str(exc)
    
    @staticmethod
    def _clean_user_profile(
        user_profile: Optional[Dict[str, str]]
    ) -> Dict[str, str]:
        """사용자 프로필에서 '선택 안 함' 또는 빈 값을 제거"""
        if not user_profile:
            return {}

        allowed_keys = {"targetGroup", "fitnessLevelName", "fitnessFactorName"}
        cleaned: Dict[str, str] = {}
        for key in allowed_keys:
            value = user_profile.get(key)
            if not value:
                continue
            normalized = value.strip()
            if not normalized or normalized == "선택 안 함":
                continue
            cleaned[key] = normalized
        return cleaned

    def _format_user_profile_block(self, profile: Dict[str, str]) -> str:
        """프롬프트에 사용할 사용자 프로필 설명을 생성"""
        if not profile:
            return (
                "제공되지 않음 (일반적인 대상/수준/목적을 기준으로 안전한 운동을 추천하세요)."
            )

        label_map = {
            "targetGroup": "대상 연령대",
            "fitnessLevelName": "운동 수준",
            "fitnessFactorName": "운동 목적",
        }
        lines = []
        for key, label in label_map.items():
            if profile.get(key):
                lines.append(f"- {label}: {profile[key]}")

        lines.append(
            "- 위 조건에 맞춰 운동 강도, 운동 종류, 주의사항을 조정하고 부적절한 움직임은 피하세요."
        )
        return "\n".join(lines)
    
    def _repair_json_response(self, raw_response: str, json_error: json.JSONDecodeError) -> Optional[Dict[str, Any]]:
        """JSON 파싱 실패 시 복구 시도"""
        try:
            # 에러 위치 확인
            error_pos = getattr(json_error, 'pos', None)
            error_msg = str(json_error)
            
            print(f"[JSON 복구] 시작 - 에러 위치: {error_pos}, 메시지: {error_msg[:100]}")
            
            # 문자열 종료되지 않은 경우 처리
            if "Unterminated string" in error_msg:
                # 방법 1: 에러 위치 이전의 마지막 완전한 문자열 필드까지 찾아서 제거
                check_limit = error_pos if error_pos else len(raw_response)
                
                # 에러 위치 이전에서 마지막 완전한 필드 끝 위치 찾기
                # 역순으로 탐색하여 완전한 JSON 구조 찾기
                for cut_pos in range(check_limit - 1, max(0, check_limit - 500), -1):
                    # cut_pos 이전까지의 문자열로 테스트
                    test_str = raw_response[:cut_pos]
                    
                    # 마지막 불완전한 필드 제거 시도
                    # 마지막 쉼표나 콜론 이후의 불완전한 부분 제거
                    last_comma = test_str.rfind(',')
                    last_colon = test_str.rfind(':')
                    last_quote = test_str.rfind('"')
                    
                    # 마지막 완전한 필드 끝 찾기
                    if last_comma > last_colon and last_comma > 0:
                        # 쉼표 이후의 불완전한 부분 제거
                        test_str = test_str[:last_comma]
                    elif last_colon > 0:
                        # 콜론 이후의 불완전한 부분 제거
                        # 콜론 이전의 필드명까지 포함
                        field_start = test_str.rfind('"', 0, last_colon)
                        if field_start > 0:
                            test_str = test_str[:field_start]
                    
                    # 중괄호/대괄호 균형 맞추기
                    open_braces = test_str.count('{') - test_str.count('}')
                    open_brackets = test_str.count('[') - test_str.count(']')
                    
                    if open_braces > 0:
                        test_str += '}' * open_braces
                    if open_brackets > 0:
                        test_str += ']' * open_brackets
                    
                    # 마지막 쉼표 제거 (JSON 객체 끝에는 쉼표가 없어야 함)
                    test_str = test_str.rstrip().rstrip(',')
                    
                    # 닫는 중괄호 추가
                    if not test_str.rstrip().endswith('}'):
                        test_str += '}'
                    
                    try:
                        result = json.loads(test_str)
                        print(f"[JSON 복구] ✅ 성공 - 불완전한 필드 제거 후 파싱 (길이: {len(test_str)})")
                        return result
                    except:
                        continue
                
                # 방법 2: 에러 위치 이전의 완전한 JSON 구조 찾기
                open_braces = 0
                open_brackets = 0
                in_string = False
                escape_next = False
                last_valid_pos = 0
                
                for i, char in enumerate(raw_response[:check_limit]):
                    if escape_next:
                        escape_next = False
                        continue
                    if char == '\\':
                        escape_next = True
                        continue
                    if char == '"' and not escape_next:
                        in_string = not in_string
                        continue
                    if in_string:
                        continue
                    
                    if char == '{':
                        open_braces += 1
                    elif char == '}':
                        open_braces -= 1
                        if open_braces == 0 and open_brackets == 0:
                            last_valid_pos = i + 1
                    elif char == '[':
                        open_brackets += 1
                    elif char == ']':
                        open_brackets -= 1
                        if open_braces == 0 and open_brackets == 0:
                            last_valid_pos = i + 1
                
                # 완전한 JSON 구조를 찾았으면 그 부분만 파싱
                if last_valid_pos > 100:
                    truncated = raw_response[:last_valid_pos]
                    try:
                        result = json.loads(truncated)
                        print(f"[JSON 복구] ✅ 성공 - 완전한 JSON 구조 파싱 (길이: {last_valid_pos})")
                        return result
                    except Exception as parse_err:
                        print(f"[JSON 복구] ⚠️ 완전한 구조 파싱 실패: {str(parse_err)}")
            
            # 중괄호 균형이 맞지 않는 경우
            brace_count = raw_response.count('{') - raw_response.count('}')
            bracket_count = raw_response.count('[') - raw_response.count(']')
            
            if brace_count > 0 or bracket_count > 0:
                print(f"[JSON 복구] 중괄호 불균형 - 중괄호: {brace_count}, 대괄호: {bracket_count}")
                # 먼저 불완전한 문자열 필드 제거 시도
                repaired = raw_response
                # 마지막 불완전한 필드 제거
                last_colon = repaired.rfind(':')
                if last_colon > 0:
                    # 콜론 이후의 불완전한 부분 제거
                    field_start = repaired.rfind('"', 0, last_colon)
                    if field_start > 0:
                        repaired = repaired[:field_start]
                        # 마지막 쉼표 제거
                        repaired = repaired.rstrip().rstrip(',')
                
                # 닫히지 않은 중괄호/대괄호 추가
                open_braces = repaired.count('{') - repaired.count('}')
                open_brackets = repaired.count('[') - repaired.count(']')
                repaired += '}' * open_braces
                repaired += ']' * open_brackets
                
                try:
                    result = json.loads(repaired)
                    print(f"[JSON 복구] ✅ 성공 - 중괄호 균형 복구")
                    return result
                except Exception as repair_err:
                    print(f"[JSON 복구] ⚠️ 중괄호 복구 실패: {str(repair_err)}")
            
            print(f"[JSON 복구] ❌ 모든 복구 시도 실패")
            return None
        except Exception as e:
            print(f"[JSON 복구] 복구 시도 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
        
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
    
    def analyze_workout_log(
        self,
        workout_log: Dict[str, Any],
        model: str = "gpt-4o-mini",
        user_profile: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        운동 일지 데이터를 분석하고 평가합니다.
        
        Args:
            workout_log: 외부 API에서 받은 운동 일지 데이터
            model: 사용할 OpenAI 모델 (기본값: "gpt-4o-mini")
            user_profile: 사용자 프로필 정보 (targetGroup, fitnessLevelName, fitnessFactorName)
            
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
            profile_data = self._clean_user_profile(user_profile)
            prompt = self._create_log_analysis_prompt(workout_log, profile_data)
            
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
        model: str = "gpt-4o-mini",
        user_profile: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        운동 일지를 기반으로 맞춤 운동 루틴을 추천합니다.
        
        Args:
            workout_log: 외부 API에서 받은 운동 일지 데이터
            days: 다음 며칠간의 루틴 (기본 7일)
            frequency: 주간 운동 빈도
            model: 사용할 OpenAI 모델 (기본값: "gpt-4o-mini")
            user_profile: 사용자 프로필 정보 (targetGroup, fitnessLevelName, fitnessFactorName)
            
        Returns:
            Dict[str, Any]: AI 추천 루틴
        """
        
        if not self.client:
            return {
                "success": False,
                "message": "OpenAI API 키가 설정되지 않았습니다."
            }
        
        try:
            rag_candidates = self._get_rag_candidates_for_routine(workout_log, frequency, user_profile=user_profile)

            # 루틴 추천 프롬프트 생성
            prompt = self._create_routine_recommendation_prompt(
                workout_log, days, frequency, rag_candidates, user_profile=user_profile
            )
            
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
        "day_1": "첫째 날 운동 부위와 목표 요약",
        "day_2": "둘째 날 운동 부위와 목표 요약",
        "day_3": "셋째 날 운동 부위와 목표 요약",
        "day_4": "넷째 날 운동 부위와 목표 요약"
    }},
    "daily_routines": [
        {{
            "day": 1,
            "focus": "해당 날짜의 핵심 목표 요약",
            "target_body_parts": ["부위1", "부위2"],
            "exercises": [
                {{
                    "exercise_id": "후보 데이터의 exercise_id 값",
                    "title": "후보 데이터의 title 값 (name 필드 대신 title 사용)",
                    "standard_title": "후보 데이터의 standard_title 값",
                    "sets": "세트 수",
                    "reps": "반복 횟수",
                    "rest": "휴식 시간",
                    "notes": "실행 팁",
                    "body_part": "후보 데이터의 body_part 값",
                    "exercise_tool": "후보 데이터의 exercise_tool 값",
                    "description": "후보 데이터의 description 값",
                    "muscles": "후보 데이터의 muscles 값",
                    "target_group": "후보 데이터의 target_group 값",
                    "fitness_factor_name": "후보 데이터의 fitness_factor_name 값",
                    "fitness_level_name": "후보 데이터의 fitness_level_name 값",
                    "video_url": "후보 데이터에서 제공한 영상 링크",
                    "video_length_seconds": "후보 데이터의 video_length_seconds 값",
                    "image_url": "후보 데이터의 image_url 값"
                }}
            ],
            "total_duration": "예상 시간(분)",
            "reference_videos": [
                {{
                    "title": "후보 운동명",
                    "video_url": "영상 링크",
                    "why": "이 영상을 추천하는 이유"
                }}
            ]
        }}
    ],
    "tips_and_precautions": "주의사항과 팁",
    "suggested_exercises": [
        {{
            "exercise_id": "후보 데이터의 exercise_id 값",
            "title": "후보 데이터의 title 값",
            "standard_title": "후보 데이터의 standard_title 값",
            "body_part": "후보 데이터의 body_part 값",
            "exercise_tool": "후보 데이터의 exercise_tool 값",
            "description": "후보 데이터의 description 값",
            "muscles": "후보 데이터의 muscles 값",
            "target_group": "후보 데이터의 target_group 값",
            "fitness_factor_name": "후보 데이터의 fitness_factor_name 값",
            "fitness_level_name": "후보 데이터의 fitness_level_name 값",
            "video_url": "후보 데이터의 video_url 값",
            "video_length_seconds": "후보 데이터의 video_length_seconds 값",
            "image_url": "후보 데이터의 image_url 값",
            "why": "추천 이유"
        }}
    ],
    "next_target_muscles": ["근육명1", "근육명2", "근육명3"]
}}

⚠️ 매우 중요 - RAG 후보 데이터 사용 규칙:
- daily_routines[].exercises[] 및 suggested_exercises[] 항목을 작성할 때는 반드시 사용자 프롬프트에 제공된 "[추천 후보 운동 데이터(JSON)]" 배열에 있는 운동만 사용하세요.
- 위 배열에 없는 운동명, video_url, image_url 등을 절대 임의로 생성하거나 만들어내지 마세요.
- 각 운동의 모든 필드(exercise_id, video_url, video_length_seconds, title, standard_title, body_part, exercise_tool, description, muscles, target_group, fitness_factor_name, fitness_level_name 등)는 반드시 제공된 JSON 배열에서 가져온 값을 그대로 사용하세요.
- title 필드를 사용하세요 (name 필드는 사용하지 마세요). title은 후보 데이터의 title 값을 그대로 사용하세요.
- muscles 필드를 사용하세요 (muscle_name이 아닙니다).
- video_url과 title/standard_title의 쌍은 제공된 JSON에서 정확히 일치하는 것을 사용하세요.
- 후보 운동 데이터를 참고해 루틴을 구성하고, 선택한 이유를 reference_videos/suggested_exercises에 명시하세요.
- next_target_muscles는 제공된 근육 라벨 목록에서만 선택하세요.
- JSON 형식을 엄격히 지키고, 누락된 필드가 없도록 하세요.
- 반드시 최소 3일(day 1 이상 연속) 이상의 daily_routines를 작성하고, 각 day마다 최소 3개 이상의 각기 다른 운동을 포함하세요.
- 하루에 한 가지 운동만 추천하거나 단일 복근운동(예: 싯업 한 가지)만 제시하지 말고, 대상/목적/수준에 맞는 다양한 운동 조합을 구성하세요."""
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
                "model": model,
                "rag_sources": rag_candidates
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"루틴 추천 중 오류 발생: {str(e)}"
            }

    def analyze_weekly_pattern_and_recommend(
        self,
        weekly_logs: List[Dict[str, Any]],
        model: str = "gpt-4o-mini",
        user_profile: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        7일치 운동 데이터를 기반으로 패턴을 분석하고 맞춤 루틴을 추천합니다.

        Args:
            weekly_logs: 날짜 역순 또는 순차 정렬된 7일치 운동 기록 리스트
            model: 사용할 OpenAI 모델 (기본값: "gpt-4o-mini")
            user_profile: 사용자 프로필 정보 (targetGroup, fitnessLevelName, fitnessFactorName)

        Returns:
            Dict[str, Any]: 패턴 분석 및 루틴 추천 결과
        """

        start_time = time.time()
        print(f"[주간 패턴 분석] 시작 - 모델: {model}, 로그 수: {len(weekly_logs)}")
        
        if not self.client:
            print("[주간 패턴 분석] ❌ OpenAI API 키가 설정되지 않음")
            return {
                "success": False,
                "message": "OpenAI API 키가 설정되지 않았습니다."
            }

        try:
            step_start = time.time()
            profile_data = self._clean_user_profile(user_profile)
            prompt, metrics = self._create_weekly_pattern_prompt(weekly_logs, profile_data)
            print(f"[주간 패턴 분석] ✅ 프롬프트 생성 완료 ({time.time() - step_start:.2f}초)")
            
            # RAG로 운동 후보 검색
            rag_start = time.time()
            rag_candidates = []
            if self.exercise_rag:
                try:
                    print(f"[주간 패턴 분석] 🔍 RAG 검색 시작...")
                    # 주간 패턴에서 부족한 부위나 추천 근육을 기반으로 RAG 검색
                    body_part_counts = metrics.get("body_part_counts", {})
                    top_muscles = metrics.get("top_muscles", [])
                    
                    # 모든 근육 사용량 계산 (부족한 근육 찾기용)
                    all_muscle_counts = {}
                    for log in weekly_logs:
                        exercises = log.get("exercises", [])
                        for ex in exercises:
                            if isinstance(ex, dict):
                                exercise_info = ex.get("exercise", {}) or {}
                                for muscle in exercise_info.get("muscles", []) or []:
                                    all_muscle_counts[muscle] = all_muscle_counts.get(muscle, 0) + 1
                    
                    # 사용자 프로필 정보를 쿼리에 포함
                    profile_prefix = ""
                    if profile_data:
                        profile_parts = []
                        if profile_data.get("targetGroup"):
                            profile_parts.append(profile_data["targetGroup"])
                        if profile_data.get("fitnessLevelName"):
                            profile_parts.append(profile_data["fitnessLevelName"])
                        if profile_data.get("fitnessFactorName"):
                            profile_parts.append(profile_data["fitnessFactorName"])
                        if profile_parts:
                            profile_prefix = " ".join(profile_parts) + " "
                    
                    print(f"[주간 패턴 분석] 👤 사용자 프로필: {profile_prefix.strip() if profile_prefix else '없음'}")
                    
                    # 여러 쿼리로 검색하여 다양한 운동 후보 수집
                    queries = []
                    
                    # 1. 적게 사용된 부위 기반
                    if body_part_counts:
                        sorted_parts = sorted(body_part_counts.items(), key=lambda x: x[1])
                        if sorted_parts:
                            least_used = sorted_parts[0][0]
                            queries.append(f"{profile_prefix}{least_used} 운동 추천")
                    
                    # 2. 적게 사용된 근육 기반 (muscles 필드 활용)
                    if all_muscle_counts:
                        sorted_muscles = sorted(all_muscle_counts.items(), key=lambda x: x[1])
                        # 가장 적게 사용된 근육 2개 선택
                        for muscle_name, count in sorted_muscles[:2]:
                            if count <= 1:  # 1회 이하로 사용된 근육
                                queries.append(f"{profile_prefix}{muscle_name} 운동")
                    
                    # 3. 많이 사용된 근육의 보완 운동
                    if top_muscles:
                        top_muscle = top_muscles[0].get("name", "")
                        if top_muscle:
                            queries.append(f"{profile_prefix}{top_muscle} 보완 운동")
                    
                    # 4. 전신 균형 운동
                    queries.append(f"{profile_prefix}전신 균형 운동")
                    
                    print(f"[주간 패턴 분석] 📝 생성된 검색 쿼리: {queries[:5]}")
                    
                    # 필터링 파라미터 설정
                    target_group_filter = None
                    exclude_target_groups = None
                    fitness_factor_filter = None
                    exclude_fitness_factors = None
                    
                    if profile_data:
                        # 대상 그룹 필터링: 성인인 경우 유소년/노인 제외
                        target_group = profile_data.get("targetGroup")
                        if target_group == "성인":
                            exclude_target_groups = ["유소년", "노인"]
                        elif target_group:
                            target_group_filter = target_group
                        
                        # 체력 요인 필터링: 근력/근지구력을 원하는 경우 유연성 제외
                        fitness_factor = profile_data.get("fitnessFactorName")
                        if fitness_factor:
                            # 근력/근지구력이 포함된 경우 유연성 제외
                            if "근력" in fitness_factor or "근지구력" in fitness_factor:
                                exclude_fitness_factors = ["유연성"]
                                fitness_factor_filter = fitness_factor
                            else:
                                fitness_factor_filter = fitness_factor
                    
                    # 여러 쿼리로 검색하여 중복 제거
                    all_candidates = []
                    seen_titles = set()
                    query_times = []
                    for idx, query in enumerate(queries[:5]):  # 최대 5개 쿼리
                        query_start = time.time()
                        try:
                            results = self.exercise_rag.search(
                                query, 
                                top_k=5,
                                target_group_filter=target_group_filter,
                                exclude_target_groups=exclude_target_groups,
                                fitness_factor_filter=fitness_factor_filter,
                                exclude_fitness_factors=exclude_fitness_factors,
                            )
                            query_elapsed = time.time() - query_start
                            query_times.append(query_elapsed)
                            print(f"[주간 패턴 분석] 🔎 쿼리 {idx+1}/{len(queries[:5])}: '{query}' - {len(results)}개 결과 ({query_elapsed:.2f}초)")
                            for item in results:
                                meta = item.get("metadata", {}) or {}
                                title = meta.get("title") or meta.get("standard_title") or ""
                                if title and title not in seen_titles:
                                    seen_titles.add(title)
                                    all_candidates.append(item)
                        except Exception as query_err:
                            print(f"[주간 패턴 분석] ⚠️ 쿼리 '{query}' 검색 실패: {str(query_err)}")
                            continue
                    
                    # 사용자 프로필에 맞게 후보 필터링 및 재정렬
                    if profile_data and all_candidates:
                        scored_candidates = []
                        for candidate in all_candidates:
                            meta = candidate.get("metadata", {}) or {}
                            score = candidate.get("score", 0.0)
                            
                            # 프로필 일치도에 따라 점수 조정
                            if profile_data.get("targetGroup"):
                                if meta.get("target_group") == profile_data["targetGroup"]:
                                    score += 0.3  # target_group 일치 시 점수 증가
                                elif meta.get("target_group") and meta.get("target_group") != profile_data["targetGroup"]:
                                    score -= 0.2  # 불일치 시 점수 감소
                            
                            if profile_data.get("fitnessLevelName"):
                                if meta.get("fitness_level_name") == profile_data["fitnessLevelName"]:
                                    score += 0.2  # fitness_level_name 일치 시 점수 증가
                            
                            if profile_data.get("fitnessFactorName"):
                                if meta.get("fitness_factor_name") == profile_data["fitnessFactorName"]:
                                    score += 0.3  # fitness_factor_name 일치 시 점수 증가
                            
                            scored_candidates.append((score, candidate))
                        
                        # 점수 순으로 정렬
                        scored_candidates.sort(key=lambda x: x[0], reverse=True)
                        all_candidates = [candidate for _, candidate in scored_candidates]
                        print(f"[주간 패턴 분석] 📊 프로필 기반 재정렬 완료 (상위 3개 점수: {[f'{scored_candidates[i][0]:.2f}' for i in range(min(3, len(scored_candidates)))]})")
                    
                    rag_candidates = all_candidates[:15]  # 최대 15개
                    rag_elapsed = time.time() - rag_start
                    print(f"[주간 패턴 분석] ✅ RAG 검색 완료 - 총 {len(rag_candidates)}개 후보 수집 ({rag_elapsed:.2f}초, 평균 쿼리: {sum(query_times)/len(query_times) if query_times else 0:.2f}초)")
                except Exception as e:
                    rag_elapsed = time.time() - rag_start
                    print(f"[주간 패턴 분석] ❌ RAG 검색 실패 ({rag_elapsed:.2f}초): {str(e)}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"[주간 패턴 분석] ⚠️ RAG 서비스 사용 불가 (exercise_rag=None)")

            api_start = time.time()
            print(f"[주간 패턴 분석] 🤖 OpenAI API 호출 시작 (모델: {model})...")
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": f"""당신은 전문 운동 코치이자 데이터 분석가입니다. 반드시 다음 JSON 형식으로만 응답하세요:

{{
    "summary_metrics": {{
        "weekly_workout_count": 0,
        "rest_days": 0,
        "total_minutes": 0,
        "intensity_counts": {{"상": 0, "중": 0, "하": 0}},
        "body_part_counts": {{"어깨": 0, "가슴": 0}},
        "top_muscles": [{{"name": "근육명", "count": 0}}]
    }},
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
                "exercises": [1, 2, 3],
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

⚠️ 매우 중요 - 응답 길이 제한:
- 전체 응답은 최대 3500 토큰(약 14000자)을 초과하지 마세요.
- 각 텍스트 필드는 간결하게 작성하세요:
  * "consistency", "intensity_trend", "comments", "habit_observation": 각각 최대 100자
  * "focus": 각 day별 최대 50자
  * "notes": 각 운동별 최대 80자
  * "progression_strategy", "recovery_guidance", "encouragement": 각각 최대 150자
  * "weekly_overview": 각 항목 최대 60자
  * "estimated_duration": "45분" 형식으로 간단히
- 불필요한 설명이나 반복을 피하고 핵심만 전달하세요.
- JSON이 완전히 닫히도록 주의하세요 (모든 중괄호와 대괄호가 올바르게 닫혀야 함).

⚠️ 매우 중요 - RAG 후보 데이터 사용 규칙:
- recommended_routine.daily_details[].exercises[] 필드는 반드시 숫자 배열로 작성하세요 (예: [1, 2, 3]).
- exercises 배열에는 후보 운동 데이터의 exercise_id 값만 포함하세요.
- exercise_id는 사용자 프롬프트에 제공된 "[추천 후보 운동 데이터(JSON)]" 배열에 있는 운동의 exercise_id 값만 사용하세요.
- 위 배열에 없는 exercise_id를 절대 임의로 생성하거나 만들어내지 마세요.
- 각 exercise_id는 반드시 제공된 JSON 배열에서 가져온 값을 그대로 사용하세요.

⚠️ 중요: next_target_muscles, muscle_balance.overworked, muscle_balance.underworked 필드는 반드시 아래 근육 라벨 목록에 정확히 포함된 이름만 사용해야 합니다.
다른 이름(예: "어깨근육", "팔근육", "복근" 등)은 절대 사용하지 마세요.
반드시 아래 목록에서 정확한 근육명을 선택하세요.

⚠️ 매우 중요 - 루틴 분량 조건:
- 반드시 최소 3일 이상의 daily_details를 작성하고, 각 day마다 반드시 최소 3개 이상의 각기 다른 운동을 포함하세요.
- 하루에 한 가지 운동만 추천하거나 단일 복근운동(예: 싯업 한 가지)만 제시하지 말고, 대상/목적/수준에 맞는 다양한 운동 조합을 구성하세요.
- 상세한 운동명, 세트, 횟수, 휴식시간까지 포함해주세요."""
                    },
                    {
                        "role": "user",
                        "content": self._add_rag_to_weekly_prompt(prompt, rag_candidates)
                    }
                ],
                temperature=0.7,
                max_tokens=3500,  # 프롬프트에서 명시한 최대 토큰 수와 일치
                response_format={"type": "json_object"}
            )
            api_elapsed = time.time() - api_start
            print(f"[주간 패턴 분석] ✅ OpenAI API 응답 수신 ({api_elapsed:.2f}초)")

            if not response or not response.choices:
                print(f"[주간 패턴 분석] ❌ OpenAI API 응답이 비어있음")
                raise Exception("OpenAI API 응답이 비어있습니다.")

            ai_response = response.choices[0].message.content
            if not ai_response:
                print(f"[주간 패턴 분석] ❌ AI 응답 내용이 비어있음")
                raise Exception("AI 응답 내용이 비어있습니다.")

            print(f"[주간 패턴 분석] 📄 AI 응답 길이: {len(ai_response)} 문자")

            parse_start = time.time()
            try:
                parsed_response = json.loads(ai_response)
                parse_elapsed = time.time() - parse_start
                print(f"[주간 패턴 분석] ✅ JSON 파싱 완료 ({parse_elapsed:.2f}초)")

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
                
                # 루틴 검증 및 운동 목록을 ID만 반환하도록 변환
                recommended_routine = parsed_response.get("recommended_routine", {})
                daily_details = recommended_routine.get("daily_details", [])
                print(f"[주간 패턴 분석] 📊 추천 루틴: {len(daily_details)}일, 총 {sum(len(day.get('exercises', [])) for day in daily_details if isinstance(day, dict))}개 운동")
                
                # 운동 목록을 exercise_id만 포함하도록 변환
                for day in daily_details:
                    if not isinstance(day, dict):
                        continue
                    exercises = day.get("exercises", [])
                    if not isinstance(exercises, list):
                        continue
                    
                    # 이미 숫자 배열인지 확인
                    if exercises and len(exercises) > 0 and isinstance(exercises[0], (int, float)):
                        # 이미 ID 배열이면 그대로 사용
                        exercise_ids = [int(ex_id) for ex_id in exercises if isinstance(ex_id, (int, float))]
                        day["exercises"] = exercise_ids
                        print(f"[주간 패턴 분석] ✅ Day {day.get('day', '?')}: 이미 ID 배열 ({len(exercise_ids)}개)")
                    else:
                        # 객체 배열이면 exercise_id만 추출
                        exercise_ids = []
                        for ex in exercises:
                            if isinstance(ex, dict):
                                ex_id = ex.get("exercise_id")
                                if ex_id is not None:
                                    exercise_ids.append(int(ex_id))
                            elif isinstance(ex, (int, float)):
                                exercise_ids.append(int(ex))
                        
                        # exercises를 ID 목록으로 교체
                        day["exercises"] = exercise_ids
                        print(f"[주간 패턴 분석] 🔄 Day {day.get('day', '?')}: {len(exercise_ids)}개 운동 ID로 변환")
                
            except json.JSONDecodeError as json_err:
                parse_elapsed = time.time() - parse_start
                print(f"[주간 패턴 분석] ❌ JSON 파싱 실패 ({parse_elapsed:.2f}초): {str(json_err)}")
                print(f"[주간 패턴 분석] 📄 응답 일부 (처음 500자): {ai_response[:500]}...")
                print(f"[주간 패턴 분석] 📄 응답 일부 (끝 500자): ...{ai_response[-500:]}")
                
                # JSON 복구 시도
                try:
                    parsed_response = self._repair_json_response(ai_response, json_err)
                    if parsed_response:
                        print(f"[주간 패턴 분석] ⚠️ JSON 복구 성공 (부분 파싱)")
                    else:
                        parsed_response = {"raw_response": ai_response, "parse_error": str(json_err)}
                except Exception as repair_err:
                    print(f"[주간 패턴 분석] ❌ JSON 복구 실패: {str(repair_err)}")
                    parsed_response = {"raw_response": ai_response, "parse_error": str(json_err)}

            total_elapsed = time.time() - start_time
            print(f"[주간 패턴 분석] ✅ 완료 - 총 소요 시간: {total_elapsed:.2f}초")
            
            return {
                "success": True,
                "result": parsed_response,
                "metrics_summary": metrics,
                "rag_sources": rag_candidates,
                "model": model
            }

        except Exception as e:
            total_elapsed = time.time() - start_time
            print(f"[주간 패턴 분석] ❌ 오류 발생 (총 {total_elapsed:.2f}초): {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"주간 패턴 분석 중 오류 발생: {str(e)}"
            }
    
    def _create_log_analysis_prompt(
        self,
        workout_log: Dict[str, Any],
        user_profile: Optional[Dict[str, str]] = None,
    ) -> str:
        """운동 일지 데이터를 프롬프트로 변환"""
        
        date = workout_log.get("date", "날짜 정보 없음")
        memo = workout_log.get("memo", "")
        exercises = workout_log.get("exercises", [])
        profile_block = self._format_user_profile_block(user_profile or {})
        
        prompt = f"""
사용자의 운동 일지를 분석해주세요.

[사용자 프로필]
{profile_block}

[운동 일지 정보]
날짜: {date}
메모: {memo}

[운동 상세]
"""
        
        for i, ex_data in enumerate(exercises, 1):
            exercise = ex_data.get("exercise", {})
            muscles_list = exercise.get('muscles', [])
            muscles_text = ', '.join(muscles_list) if muscles_list else '정보 없음'
            prompt += f"""
운동 {i}:
- 운동명: {exercise.get('title', 'N/A')}
- 근육 부위: {muscles_text}
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
6. 사용자 프로필(targetGroup, fitnessLevelName, fitnessFactorName)이 제공되면 해당 조건에 맞는 운동 강도와 목적만 추천하고, 제공되지 않으면 일반적인 안전 기준을 따르세요.

[근육 라벨 목록]
아래 목록에 포함된 근육명만 사용하여 다음 운동을 추천할 근육(next_target_muscles)을 2~5개 선정하세요.
선정 기준: (1) 최근 기록에서 부족하거나 덜 사용된 근육, (2) 과사용 부위는 피함, (3) 전신 균형 개선.
{', '.join(MUSCLE_LABELS)}

친근하고 격려하는 톤으로 작성해주세요."""
        
        return prompt

    def _get_rag_candidates_for_routine(
        self,
        workout_log: Dict[str, Any],
        frequency: int,
        user_profile: Optional[Dict[str, str]] = None,
        top_k: int = 6
    ) -> List[Dict[str, Any]]:
        if not self.exercise_rag:
            return []

        query = self._build_rag_query(workout_log, frequency, user_profile=user_profile)
        if not query:
            return []

        try:
            # 필터링 파라미터 설정
            target_group_filter = None
            exclude_target_groups = None
            fitness_factor_filter = None
            exclude_fitness_factors = None
            
            if user_profile:
                # 대상 그룹 필터링: 성인인 경우 유소년/노인 제외
                target_group = user_profile.get("targetGroup")
                if target_group == "성인":
                    exclude_target_groups = ["유소년", "노인"]
                elif target_group:
                    target_group_filter = target_group
                
                # 체력 요인 필터링: 근력/근지구력을 원하는 경우 유연성 제외
                fitness_factor = user_profile.get("fitnessFactorName")
                if fitness_factor:
                    # 근력/근지구력이 포함된 경우 유연성 제외
                    if "근력" in fitness_factor or "근지구력" in fitness_factor:
                        exclude_fitness_factors = ["유연성"]
                        fitness_factor_filter = fitness_factor
                    else:
                        fitness_factor_filter = fitness_factor
            
            return self.exercise_rag.search(
                query, 
                top_k=top_k,
                target_group_filter=target_group_filter,
                exclude_target_groups=exclude_target_groups,
                fitness_factor_filter=fitness_factor_filter,
                exclude_fitness_factors=exclude_fitness_factors,
            )
        except Exception:
            return []

    def _build_rag_query(
        self,
        workout_log: Dict[str, Any],
        frequency: int,
        user_profile: Optional[Dict[str, str]] = None,
    ) -> str:
        exercises = workout_log.get("exercises") or []
        muscles: List[str] = []
        body_parts: List[str] = []

        for ex in exercises:
            if not isinstance(ex, dict):
                continue
            exercise_info = ex.get("exercise", {}) or {}
            muscles.extend(exercise_info.get("muscles", []) or [])
            body_part = exercise_info.get("bodyPart")
            if body_part:
                body_parts.append(body_part)

        muscles = [m for m in {m for m in muscles if m}]
        body_parts = [bp for bp in {bp for bp in body_parts if bp}]

        focus_clause = ""
        if body_parts:
            focus_clause = f"주요 운동 부위: {', '.join(body_parts)}. "
        elif muscles:
            focus_clause = f"목표 근육: {', '.join(muscles)}. "

        profile_parts: List[str] = []
        if user_profile:
            if user_profile.get("targetGroup"):
                profile_parts.append(f"대상 연령: {user_profile['targetGroup']}")
            if user_profile.get("fitnessLevelName"):
                profile_parts.append(f"운동 수준: {user_profile['fitnessLevelName']}")
            if user_profile.get("fitnessFactorName"):
                profile_parts.append(f"운동 목적: {user_profile['fitnessFactorName']}")

        profile_clause = " ".join(profile_parts)
        frequency_clause = f"주 {frequency}회 루틴에 적합한 운동을 추천."

        query_parts = [focus_clause, profile_clause, frequency_clause]
        return " ".join(part for part in query_parts if part).strip()
    
    def _create_routine_recommendation_prompt(
        self, 
        workout_log: Dict[str, Any], 
        days: int, 
        frequency: int,
        rag_candidates: Optional[List[Dict[str, Any]]] = None,
        user_profile: Optional[Dict[str, str]] = None,
    ) -> str:
        """운동 루틴 추천을 위한 프롬프트 생성"""
        
        date = workout_log.get("date", "날짜 정보 없음")
        exercises = workout_log.get("exercises", [])
        profile_block = self._format_user_profile_block(user_profile or {})
        
        # 근육 그룹 추출
        muscle_groups = []
        for ex_data in exercises:
            exercise = ex_data.get("exercise", {})
            muscles = exercise.get("muscles", [])
            muscle_groups.extend(muscles)
        
        unique_muscles = list(set(muscle_groups))
        
        # RAG 후보 데이터를 메타데이터만 추출하여 포맷팅
        candidate_payload = []
        if rag_candidates:
            for item in rag_candidates:
                meta = item.get("metadata", {}) or {}
                candidate_payload.append({
                    "score": item.get("score"),
                    "exercise_id": meta.get("exercise_id"),  # exercise_id 추가
                    "title": meta.get("title"),
                    "standard_title": meta.get("standard_title"),
                    "training_name": meta.get("training_name"),
                    "body_part": meta.get("body_part"),
                    "exercise_tool": meta.get("exercise_tool"),
                    "fitness_factor_name": meta.get("fitness_factor_name"),
                    "fitness_level_name": meta.get("fitness_level_name"),
                    "target_group": meta.get("target_group"),
                    "training_aim_name": meta.get("training_aim_name"),
                    "training_place_name": meta.get("training_place_name"),
                    "training_section_name": meta.get("training_section_name"),
                    "training_step_name": meta.get("training_step_name"),
                    "description": meta.get("description"),
                    "muscles": meta.get("muscles"),  # 근육 정보 추가
                    "video_url": meta.get("video_url"),
                    "video_length_seconds": meta.get("video_length_seconds"),  # video_length_seconds 추가
                    "image_url": meta.get("image_url"),
                    "image_file_name": meta.get("image_file_name"),  # image_file_name 추가
                })
        candidate_json = json.dumps(candidate_payload, ensure_ascii=False, indent=2)

        prompt = f"""
사용자의 최근 운동 기록:
날짜: {date}

[사용자 프로필]
{profile_block}

주요 근육 그룹:
{', '.join(unique_muscles) if unique_muscles else '기록 없음'}

주 {frequency}회, {days}일간의 운동 루틴을 작성해주세요.

사용자의 운동 수준과 패턴을 고려하여:
- 전신 균형을 고려한 분할 방식
- 적절한 운동 강도와 빈도
- 점진적 과부하 원칙
- 안전하고 실천 가능한 루틴
- 사용자 프로필(targetGroup, fitnessLevelName, fitnessFactorName)이 제공되면 그 조건에 맞는 운동만 선택하세요. 정보가 없으면 일반적인 안전 기준을 따르세요.
- 반드시 최소 3일 이상의 분할(day 1~)을 구성하고, 각 day마다 최소 3개 이상의 각기 다른 운동을 포함하세요. 단일 운동만 추천하지 마세요.

상세한 운동명, 세트, 횟수, 휴식시간까지 포함해주세요.

[추천 후보 운동 데이터(JSON)]
{candidate_json}

⚠️ 매우 중요: daily_routines[].exercises[] 및 suggested_exercises[] 항목을 작성할 때는 반드시 위 JSON 배열에 있는 운동 데이터만 사용하세요.
- exercises 배열의 각 항목은 위 JSON 배열의 항목 중 하나를 선택하여 사용해야 합니다.
- title 필드를 사용하세요 (name 필드는 사용하지 마세요). title은 후보 데이터의 title 값을 사용하세요.
- exercise_id, video_url, video_length_seconds, image_url, body_part, exercise_tool, description, muscles, target_group, fitness_factor_name, fitness_level_name 등 모든 필드는 위 JSON에서 제공된 값을 그대로 사용하세요.
- 위 JSON에 없는 운동명, video_url, image_url 등을 임의로 생성하거나 만들어내지 마세요.
- 위 JSON 배열에 있는 운동만 추천하고, 배열에 없는 운동은 절대 추가하지 마세요.
- 각 운동의 video_url과 title/standard_title은 반드시 위 JSON에서 제공된 쌍을 그대로 사용하세요.
- muscles 필드를 사용하세요 (muscle_name이 아닙니다).

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

    def _calculate_weekly_metrics(self, weekly_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        intensity_counts: Dict[str, int] = {"상": 0, "중": 0, "하": 0}
        body_part_counts: Dict[str, int] = {}
        muscle_counts: Dict[str, int] = {}
        total_minutes = 0
        active_days = 0

        for log in weekly_logs:
            raw_exercises = log.get("exercises")

            if isinstance(raw_exercises, list):
                exercises = [ex for ex in raw_exercises if isinstance(ex, dict)]
            elif isinstance(raw_exercises, dict):
                exercises = [raw_exercises]
            else:
                exercises = []

            if exercises:
                active_days += 1

            for ex in exercises:
                intensity = ex.get("intensity", "중")
                if intensity not in intensity_counts:
                    intensity_counts.setdefault("기타", 0)
                    intensity_counts["기타"] += 1
                else:
                    intensity_counts[intensity] += 1

                total_minutes += ex.get("exerciseTime", 0)

                exercise_info = ex.get("exercise", {})
                body_part = exercise_info.get("bodyPart") or self._infer_body_part(exercise_info)
                body_part_counts[body_part] = body_part_counts.get(body_part, 0) + 1

                for muscle in exercise_info.get("muscles", []):
                    muscle_counts[muscle] = muscle_counts.get(muscle, 0) + 1

        top_muscles = [
            {"name": name, "count": count}
            for name, count in sorted(muscle_counts.items(), key=lambda item: item[1], reverse=True)
        ]

        # 주간 분석이므로 총 일수는 항상 7일로 고정
        rest_days = max(0, 7 - active_days)

        return {
            "weekly_workout_count": active_days,
            "rest_days": rest_days,
            "total_minutes": total_minutes,
            "intensity_counts": intensity_counts,
            "body_part_counts": body_part_counts,
            "top_muscles": top_muscles
        }

    def _infer_body_part(self, exercise_info: Dict[str, Any]) -> str:
        title = exercise_info.get("title", "").lower()
        description = exercise_info.get("description", "").lower()
        training_name = exercise_info.get("trainingName", "").lower()

        lower_body_keywords = [
            "다리", "하체", "스쿼트", "런지", "데드", "레그", "대퇴", "허벅지", "종아리", "힙", "볼기", "둔근"
        ]
        upper_body_keywords = [
            "가슴", "어깨", "팔", "등", "코어", "복부", "벤치", "프레스", "풀업", "랫", "로우"
        ]

        text = " ".join(filter(None, [title, description, training_name]))

        if any(keyword in text for keyword in lower_body_keywords):
            return "하체"
        if any(keyword in text for keyword in upper_body_keywords):
            return "상체"

        return "기타"

    def _create_weekly_pattern_prompt(
        self,
        weekly_logs: List[Dict[str, Any]],
        user_profile: Optional[Dict[str, str]] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """7일치 운동 기록을 프롬프트로 변환"""

        if not weekly_logs:
            return (
                "최근 7일간의 운동 기록이 제공되지 않았습니다. 가능한 경우 최근 기록을 기반으로 통찰과 루틴을 제안해주세요.",
                {
                    "weekly_workout_count": 0,
                    "rest_days": 7,
                    "total_minutes": 0,
                    "intensity_counts": {"상": 0, "중": 0, "하": 0},
                    "body_part_counts": {},
                    "top_muscles": []
                }
            )

        metrics = self._calculate_weekly_metrics(weekly_logs)
        profile_block = self._format_user_profile_block(user_profile or {})

        intensity_summary_items = [
            f"{level} {count}회" for level, count in metrics["intensity_counts"].items()
        ]
        intensity_summary = ", ".join(intensity_summary_items) if intensity_summary_items else "데이터 없음"

        sorted_body_parts = sorted(
            metrics["body_part_counts"].items(),
            key=lambda item: item[1],
            reverse=True
        )
        body_part_summary = ", ".join(
            f"{bp} {cnt}회" for bp, cnt in sorted_body_parts[:6]
        ) if sorted_body_parts else "데이터 없음"

        top_muscle_summary = ", ".join(
            f"{entry['name']} {entry['count']}회" for entry in metrics.get("top_muscles", [])[:6]
        ) if metrics.get("top_muscles") else "데이터 없음"

        prompt = f"""
사용자의 최근 7일 운동 기록을 분석하고, 패턴을 파악해 적절한 루틴을 제안해주세요.

[사용자 프로필]
{profile_block}

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
                        muscles_list = exercise.get('muscles', [])
                        muscles_text = ', '.join(muscles_list) if muscles_list else '정보 없음'
                        prompt += f"- 운동 {ex_idx}: {exercise.get('title', '운동명 없음')} | 사용 근육: {muscles_text} | 강도: {ex_data.get('intensity', '정보 없음')} | 시간: {ex_data.get('exerciseTime', 0)}분 | 도구: {exercise.get('exerciseTool', '정보 없음')}\n"

        prompt += f"""

[주간 요약 지표]
- 주간 운동 횟수: {metrics['weekly_workout_count']}회
- 총 운동 시간: {metrics['total_minutes']}분
- 강도 분포: {intensity_summary}
- 주요 운동 부위: {body_part_summary}
- 상위 근육 사용: {top_muscle_summary}
- 휴식일 수: {metrics['rest_days']}일

[분석 및 추천 지침]
1. 주간 운동 빈도, 강도, 회복 상태를 종합 분석
2. 근육 사용량의 불균형, 과사용/부족 부위를 명확히 제시
3. 다음 주를 위한 4~6회 분할 루틴을 구성하고 휴식일 또는 액티브 리커버리 제안 포함
4. 점진적 과부하 전략과 컨디션 조절 팁 포함
5. 회복을 돕는 생활 습관(수면, 영양, 스트레칭) 권장 사항 제시
6. 사용자 프로필(targetGroup, fitnessLevelName, fitnessFactorName)이 제공되면 해당 조건에 적합한 난이도/운동 종류만 우선 추천하고, 부적절한 종목은 피하세요.
7. 반드시 최소 3일 이상의 분할을 구성하고, 각 day마다 반드시 최소 3개 이상의 각기 다른 운동을 포함하세요. 상세한 운동명, 세트, 횟수, 휴식시간까지 포함해주세요.

[근육 라벨 목록]
아래 목록에 포함된 근육명만 사용하여 muscle_balance.overworked, muscle_balance.underworked, next_target_muscles 항목을 구성하세요.
{', '.join(MUSCLE_LABELS)}

친근하고 격려하는 톤으로 작성하되, 실행 가능한 구체적인 정보를 제공해주세요.
"""

        return prompt, metrics

    def _add_rag_to_weekly_prompt(self, prompt: str, rag_candidates: List[Dict[str, Any]]) -> str:
        """주간 패턴 프롬프트에 RAG 후보 운동 데이터(JSON) 추가"""
        if not rag_candidates:
            return prompt

        candidate_payload: List[Dict[str, Any]] = []
        for item in rag_candidates:
            meta = item.get("metadata", {}) or {}
            candidate_payload.append(
                {
                    "score": item.get("score"),
                    "exercise_id": meta.get("exercise_id"),
                    "title": meta.get("title"),
                    "standard_title": meta.get("standard_title"),
                    "training_name": meta.get("training_name"),
                    "body_part": meta.get("body_part"),
                    "exercise_tool": meta.get("exercise_tool"),
                    "fitness_factor_name": meta.get("fitness_factor_name"),
                    "fitness_level_name": meta.get("fitness_level_name"),
                    "target_group": meta.get("target_group"),
                    "training_aim_name": meta.get("training_aim_name"),
                    "training_place_name": meta.get("training_place_name"),
                    "training_section_name": meta.get("training_section_name"),
                    "training_step_name": meta.get("training_step_name"),
                    "description": meta.get("description"),
                    "muscles": meta.get("muscles"),  # 근육 정보 추가
                    "video_url": meta.get("video_url"),
                    "video_length_seconds": meta.get("video_length_seconds"),  
                    "image_url": meta.get("image_url"),
                    "image_file_name": meta.get("image_file_name"), # image_file_name 추가
                }
            )

        rag_section = (
            "\n\n[추천 후보 운동 데이터(JSON)]\n"
            f"{json.dumps(candidate_payload, ensure_ascii=False, indent=2)}\n\n"
            "⚠️ 매우 중요: recommended_routine.daily_details[].exercises[] 항목을 작성할 때는 반드시 위 JSON 배열에 있는 운동 데이터만 사용하세요.\n"
            "- exercises 배열의 각 항목은 위 JSON 배열의 항목 중 하나를 선택하여 사용해야 합니다.\n"
            "- title 필드는 후보 데이터의 title 값을 사용하세요 (name 필드는 사용하지 마세요).\n"
            "- exercise_id, video_url, video_length_seconds, image_url, body_part, exercise_tool, description, muscles, target_group, fitness_factor_name, fitness_level_name, image_file_name 등 모든 필드는 위 JSON에서 제공된 값을 그대로 사용하세요.\n"
            "- 위 JSON에 없는 운동명, video_url, image_url 등을 임의로 생성하거나 만들어내지 마세요.\n"
            "- image_file_name과 image_url은 서로 다른 필드입니다. 반드시 각각 값을 넣으세요.\n"
            "- 위 JSON 배열에 있는 운동만 추천하고, 배열에 없는 운동은 절대 추가하지 마세요.\n"
            "- 각 운동의 video_url과 title/standard_title은 반드시 위 JSON에서 제공된 쌍을 그대로 사용하세요.\n"
            "- muscles 필드를 사용하세요 (muscle_name이 아닙니다).\n"
        )

        return prompt + rag_section


# 전역 서비스 인스턴스
openai_service = OpenAIService()
