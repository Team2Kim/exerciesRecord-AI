"""
OpenAI API 서비스
파인튜닝된 LLM을 활용한 운동 관련 AI 서비스
"""

from openai import OpenAI
import os
import json
import time
import re
from typing import Optional, Dict, Any, List, Tuple, Set
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
    
    # 둔근/볼기근 관련
    "볼기근": ["큰볼기근", "중간볼기근", "작은볼기근"],
    "둔근": ["큰볼기근", "중간볼기근", "작은볼기근"],
    
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

    def _build_rag_filter_options(
        self, profile_data: Optional[Dict[str, str]]
    ) -> Dict[str, Optional[Any]]:
        """사용자 프로필 기반 RAG 필터 옵션 구성"""
        filters: Dict[str, Optional[Any]] = {
            "target_group_filter": None,
            "exclude_target_groups": None,
            "fitness_factor_filter": None,
            "exclude_fitness_factors": None,
        }

        if not profile_data:
            return filters

        target_group = profile_data.get("targetGroup")
        if target_group == "성인":
            filters["exclude_target_groups"] = ["유소년", "노인"]
        elif target_group:
            filters["target_group_filter"] = target_group

        fitness_factor = profile_data.get("fitnessFactorName")
        if fitness_factor:
            filters["fitness_factor_filter"] = fitness_factor
            if "근력" in fitness_factor or "근지구력" in fitness_factor:
                filters["exclude_fitness_factors"] = ["유연성"]

        return filters

    def _build_profile_prefix(self, profile_data: Optional[Dict[str, str]]) -> str:
        """RAG 검색 쿼리용 사용자 프로필 텍스트"""
        if not profile_data:
            return ""

        profile_parts: List[str] = []
        if profile_data.get("targetGroup"):
            profile_parts.append(profile_data["targetGroup"])
        if profile_data.get("fitnessLevelName"):
            profile_parts.append(profile_data["fitnessLevelName"])
        if profile_data.get("fitnessFactorName"):
            profile_parts.append(profile_data["fitnessFactorName"])

        return " ".join(profile_parts).strip()

    def _normalize_tool_category(self, tool: Optional[str]) -> str:
        """운동 도구를 지정된 범주로 정규화"""
        if not tool:
            return "기타"

        normalized = tool.strip().lower()
        if not normalized:
            return "기타"

        category_keywords = {
            "맨몸": ["맨몸", "바디웨이트", "bodyweight", "체중", "무도구"],
            "의자": ["의자", "chair", "벤치"],
            "짐볼": ["짐볼", "짐 볼", "gym ball", "stability ball", "피트니스 볼"],
            "폼롤러": ["폼롤러", "foam roller", "foam-roller", "마사지 롤러", "스트레칭 롤러"],
            "탄력밴드": ["탄력밴드", "밴드", "band", "resistance band", "튜빙"],
        }

        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in normalized:
                    return category

        return "기타"

    def _extract_recent_exercise_context(
        self,
        weekly_logs: List[Dict[str, Any]],
        limit: int = 20,
    ) -> Dict[str, Any]:
        """최근 일지에 포함된 운동 정보를 추출하여 RAG 검색 시 참고"""
        titles: List[str] = []
        tool_names: List[str] = []
        tool_counts: Dict[str, int] = {
            "맨몸": 0,
            "의자": 0,
            "짐볼": 0,
            "폼롤러": 0,
            "탄력밴드": 0,
            "기타": 0,
        }

        for log in weekly_logs:
            exercises = log.get("exercises") or []
            for ex in exercises:
                if not isinstance(ex, dict):
                    continue
                exercise_info = ex.get("exercise", {}) or {}
                title = exercise_info.get("title")
                 tool_name = exercise_info.get("exerciseTool")
                 tool_category = self._normalize_tool_category(tool_name)
                 tool_counts[tool_category] = tool_counts.get(tool_category, 0) + 1
                 if tool_name:
                     stripped_tool = tool_name.strip()
                     if stripped_tool:
                         tool_names.append(stripped_tool)
                if title:
                    normalized = title.strip()
                    if normalized:
                        titles.append(normalized)

        unique_titles: List[str] = []
        seen: Set[str] = set()
        for title in titles:
            lowered = title.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            unique_titles.append(title)
            if len(unique_titles) >= limit:
                break

        unique_tools: List[str] = []
        tool_seen: Set[str] = set()
        for tool in tool_names:
            lowered = tool.lower()
            if lowered in tool_seen:
                continue
            tool_seen.add(lowered)
            unique_tools.append(tool)
            if len(unique_tools) >= limit:
                break

        preferred_tool_category = None
        significant_counts = {
            category: count for category, count in tool_counts.items() if category != "기타"
        }
        if significant_counts:
            best_category = max(significant_counts, key=significant_counts.get)
            if significant_counts[best_category] > 0:
                preferred_tool_category = best_category

        return {
            "titles": unique_titles,
            "title_set": seen,
            "tool_names": unique_tools,
            "preferred_tool_category": preferred_tool_category,
        }

    def _generate_diverse_queries(
        self,
        muscle: str,
        profile_prefix: str = "",
        extra_tags: Optional[List[str]] = None,
        max_variations: int = 5,
    ) -> List[str]:
        """동일 근육에 대해 다양한 검색 쿼리를 생성"""
        base = f"{profile_prefix} {muscle}".strip()
        descriptors = [
            "근력 강화 운동",
            "안정성 향상 루틴",
            "맨몸 운동",
            "덤벨 루틴",
            "밸런스 트레이닝",
            "저강도 회복",
            "고강도 인터벌",
            "모빌리티 스트레칭",
        ]

        if extra_tags:
            descriptors.extend(extra_tags)

        queries: List[str] = []
        seen: Set[str] = set()

        for desc in descriptors:
            candidate = f"{base} {desc}".strip()
            if candidate not in seen:
                seen.add(candidate)
                queries.append(candidate)
            if len(queries) >= max_variations:
                break

        # 기본 루틴/운동 쿼리도 포함
        fallback_queries = [
            f"{base} 운동 루틴",
            f"{base} 운동",
        ]
        for candidate in fallback_queries:
            if candidate not in seen:
                queries.append(candidate)
                seen.add(candidate)

        return queries[:max_variations]

    def _expand_muscle_aliases(self, muscle: str) -> List[str]:
        """특정 근육명과 연관된 다양한 명칭/세부 근육을 반환"""
        aliases = {muscle.strip()}

        if muscle in MUSCLE_NAME_MAPPING:
            aliases.update(MUSCLE_NAME_MAPPING[muscle])

        for label in MUSCLE_LABELS:
            if muscle in label or label in muscle:
                aliases.add(label)

        return [alias for alias in aliases if alias]

    def _metadata_matches_muscle(
        self, meta_muscles: Any, alias_tokens: List[str]
    ) -> bool:
        """메타데이터의 근육 정보가 원하는 근육 명칭과 일치하는지 확인"""
        if not meta_muscles or not alias_tokens:
            return False

        if isinstance(meta_muscles, str):
            normalized = re.split(r"[,\n/]", meta_muscles)
            candidates = [token.strip().lower() for token in normalized if token.strip()]
        elif isinstance(meta_muscles, list):
            candidates = [str(token).strip().lower() for token in meta_muscles if token]
        else:
            candidates = [str(meta_muscles).strip().lower()]

        alias_set = {alias.strip().lower() for alias in alias_tokens if alias}
        if not alias_set:
            return False

        for candidate in candidates:
            for alias in alias_set:
                if not alias or not candidate:
                    continue
                if alias in candidate or candidate in alias:
                    return True

        return False

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
                        # next_target 근육에 맞는 RAG 운동 추가
                        rag_exercises = self._search_exercises_for_muscles(
                            validated_muscles,
                            profile_data,
                            per_muscle=3,
                        )
                        if rag_exercises:
                            parsed_analysis["next_target_exercises"] = rag_exercises
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
        day_level_exercise_ids: List[int] = []
        rag_candidates: List[Dict[str, Any]] = []
        muscle_analysis: Optional[Dict[str, Any]] = None
        
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
            recent_exercise_context = self._extract_recent_exercise_context(weekly_logs)
            print(f"[주간 패턴 분석] ✅ 프롬프트 생성 완료 ({time.time() - step_start:.2f}초)")
            
            if not self.exercise_rag:
                print(f"[주간 패턴 분석] ⚠️ RAG 서비스 사용 불가 (exercise_rag=None)")

            # 3단계: 전체 분석 및 루틴 추천 (RAG 후보 없이)
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
                    "target_muscles": ["근육명1", "근육명2"],
                "exercises": [],
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
- 전체 응답은 최대 4000 토큰(약 16000자)을 초과하지 마세요.
- 각 텍스트 필드는 충분히 상세하게 작성하세요:
  * "consistency": 최대 300자 (훈련 빈도와 규칙성에 대한 상세한 분석)
  * "intensity_trend": 최대 300자 (강도 변화와 피로 누적에 대한 상세한 평가)
  * "comments": 최대 250자 (근육 사용 균형에 대한 종합 의견)
  * "habit_observation": 최대 250자 (생활 패턴 및 회복 습관 관련 상세한 인사이트)
  * "focus": 각 day별 최대 100자 (주요 부위 및 목표에 대한 설명)
  * "notes": 각 운동별 최대 120자 (운동 수행 시 주의사항이나 팁)
  * "progression_strategy": 최대 300자 (점진적 과부하 또는 변화를 위한 상세한 전략)
  * "recovery_guidance": 최대 300자 (영양, 수면, 스트레칭 등 회복 팁을 상세히)
  * "encouragement": 최대 250자 (격려 메시지)
  * "weekly_overview": 각 항목 최대 120자 (요일별 주요 타겟과 목표를 상세히)
  * "estimated_duration": "45분" 형식으로 간단히
- 충분히 상세하고 도움이 되는 설명을 작성하되, 불필요한 반복은 피하세요.
- JSON이 완전히 닫히도록 주의하세요 (모든 중괄호와 대괄호가 올바르게 닫혀야 함).

⚠️ 중요: next_target_muscles, muscle_balance.overworked, muscle_balance.underworked 필드는 반드시 아래 근육 라벨 목록에 정확히 포함된 이름만 사용해야 합니다.
다른 이름(예: "어깨근육", "팔근육", "복근" 등)은 절대 사용하지 마세요.
반드시 아래 목록에서 정확한 근육명을 선택하세요.

⚠️ 매우 중요 - 루틴 분량 조건:
- 반드시 최소 3일 이상의 daily_details를 작성하세요.
- daily_details[].target_muscles 필드는 MUSCLE_LABELS에 포함된 명칭 2~4개로 작성하세요.
- daily_details[].exercises[] 필드는 빈 배열로 두세요. 이후 시스템이 RAG 검색 결과로 채웁니다.
- 각 day의 focus와 estimated_duration은 작성하되, 구체적인 운동 목록은 포함하지 마세요."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=4000,  # 프롬프트에서 명시한 최대 토큰 수와 일치
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
                            # next_target 근육에 맞는 RAG 운동 추가
                            if validated and self.exercise_rag:
                                try:
                                    next_target_exercises = self._search_exercises_for_muscles(
                                        validated,
                                        profile_data,
                                        per_muscle=3,
                                    )
                                    if next_target_exercises:
                                        parsed_response["next_target_exercises"] = next_target_exercises
                                        print(f"[주간 패턴 분석] ✅ next_target_exercises 생성 완료: {len(next_target_exercises)}개 근육별 운동")
                                except Exception as e:
                                    print(f"[주간 패턴 분석] ⚠️ next_target_exercises 생성 실패: {str(e)}")
                        else:
                            muscle_balance = parsed_response.setdefault("pattern_analysis", {}).setdefault("muscle_balance", {})
                            muscle_balance[field_name] = validated
                
                # 루틴 검증 (exercises는 후처리 RAG 결과로 채움)
                recommended_routine = parsed_response.get("recommended_routine", {})
                daily_details = recommended_routine.get("daily_details", [])
                print(f"[주간 패턴 분석] 📊 추천 루틴: {len(daily_details)}일")
                
                # exercises 필드는 기본적으로 빈 배열로 설정
                for day in daily_details:
                    if not isinstance(day, dict):
                        continue
                    # exercises 필드가 없거나 비어있으면 빈 배열로 설정
                    if "exercises" not in day or not day.get("exercises"):
                        day["exercises"] = []

                day_level_exercise_ids = []
                if daily_details:
                    (
                        day_level_exercise_ids,
                        rag_candidates,
                    ) = self._populate_daily_details_with_exercises(
                        daily_details,
                        profile_data,
                        fallback_muscles=parsed_response.get("next_target_muscles"),
                        recent_context=recent_exercise_context,
                    )

                muscle_analysis = self._build_muscle_analysis_from_response(parsed_response)
                
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
            
            # RAG 검색 결과를 exercise_id만 추출
            recommended_exercise_ids: List[int] = []
            if rag_candidates:
                for candidate in rag_candidates:
                    meta = candidate.get("metadata", {}) or {}
                    exercise_id = meta.get("exercise_id")
                    if exercise_id is not None:
                        try:
                            recommended_exercise_ids.append(int(exercise_id))
                        except (TypeError, ValueError):
                            continue

            if day_level_exercise_ids:
                recommended_exercise_ids.extend(day_level_exercise_ids)

            if recommended_exercise_ids:
                deduped_ids: List[int] = []
                seen_ids: Set[int] = set()
                for ex_id in recommended_exercise_ids:
                    if not isinstance(ex_id, int):
                        continue
                    if ex_id in seen_ids:
                        continue
                    seen_ids.add(ex_id)
                    deduped_ids.append(ex_id)
                recommended_exercise_ids = deduped_ids
            
            return {
                "success": True,
                "result": parsed_response,
                "metrics_summary": metrics,
                "rag_sources": rag_candidates,  # 원본 RAG 결과 (전체 정보 포함, 하위 호환성)
                "recommended_exercises": recommended_exercise_ids,  # RAG 검색 결과 (exercise_id만)
                "muscle_analysis": muscle_analysis,  # LLM 근육 분석 결과
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

    def _search_exercises_for_muscles(
        self,
        muscles: List[str],
        profile_data: Optional[Dict[str, str]] = None,
        per_muscle: int = 3,
    ) -> Dict[str, List[int]]:
        """next_target_muscles에 맞는 운동을 RAG로 검색"""
        if not self.exercise_rag or not muscles:
            return {}

        filters = self._build_rag_filter_options(profile_data)
        muscle_exercises: Dict[str, List[int]] = {}

        for muscle in muscles:
            query = f"{muscle} 강화 운동"
            alias_tokens = self._expand_muscle_aliases(muscle)
            try:
                rag_results = self.exercise_rag.search(
                    query,
                    top_k=per_muscle,
                    target_group_filter=filters["target_group_filter"],
                    exclude_target_groups=filters["exclude_target_groups"],
                    fitness_factor_filter=filters["fitness_factor_filter"],
                    exclude_fitness_factors=filters["exclude_fitness_factors"],
                )
            except Exception as exc:
                print(f"[RAG] ⚠️ '{muscle}' 검색 실패: {exc}")
                continue

            exercise_ids: List[int] = []
            for item in rag_results:
                meta = item.get("metadata") or {}
                ex_id = meta.get("exercise_id")
                if ex_id is None:
                    continue

                if not self._metadata_matches_muscle(meta.get("muscles"), alias_tokens):
                    continue

                try:
                    exercise_ids.append(int(ex_id))
                except (TypeError, ValueError):
                    continue

                if len(exercise_ids) >= per_muscle:
                    break

            if exercise_ids:
                muscle_exercises[muscle] = exercise_ids

        return muscle_exercises

    def _format_rag_exercise_payload(
        self,
        metadata: Dict[str, Any],
        score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """RAG 검색 결과를 루틴에서 사용할 형태로 정규화"""
        return {
            "exercise_id": metadata.get("exercise_id"),
            "title": metadata.get("title"),
            "standard_title": metadata.get("standard_title"),
            "training_name": metadata.get("training_name"),
            "body_part": metadata.get("body_part"),
            "exercise_tool": metadata.get("exercise_tool"),
            "fitness_factor_name": metadata.get("fitness_factor_name"),
            "fitness_level_name": metadata.get("fitness_level_name"),
            "target_group": metadata.get("target_group"),
            "training_aim_name": metadata.get("training_aim_name"),
            "training_place_name": metadata.get("training_place_name"),
            "training_section_name": metadata.get("training_section_name"),
            "training_step_name": metadata.get("training_step_name"),
            "description": metadata.get("description"),
            "muscles": metadata.get("muscles"),
            "video_url": metadata.get("video_url"),
            "video_length_seconds": metadata.get("video_length_seconds"),
            "image_url": metadata.get("image_url"),
            "image_file_name": metadata.get("image_file_name"),
            "score": score,
        }

    def _search_day_exercises_with_rag(
        self,
        target_muscles: List[str],
        profile_data: Optional[Dict[str, str]] = None,
        per_day: int = 4,
        recent_context: Optional[Dict[str, Any]] = None,
        global_exclude_ids: Optional[Set[int]] = None,
        allow_reuse: bool = False,
    ) -> List[Dict[str, Any]]:
        """루틴 일자별 타겟 근육을 기반으로 실제 운동 메타데이터를 검색"""
        if not self.exercise_rag or not target_muscles:
            return []

        filters = self._build_rag_filter_options(profile_data)
        profile_prefix = self._build_profile_prefix(profile_data)
        seen_ids: Set[int] = set()
        day_exercises: List[Dict[str, Any]] = []
        recent_titles = (recent_context or {}).get("titles", []) or []
        recent_tools = (recent_context or {}).get("tool_names", []) or []
        preferred_tool_category = (recent_context or {}).get("preferred_tool_category")
        extra_tags: List[str] = []
        for title in recent_titles[:3]:
            extra_tags.append(f"{title} 대체 운동")
            extra_tags.append(f"{title} 변형 루틴")
        for tool_name in recent_tools[:3]:
            extra_tags.append(f"{tool_name} 응용 운동")
            extra_tags.append(f"{tool_name} 활용 루틴")
        if preferred_tool_category:
            extra_tags.append(f"{preferred_tool_category} 도구 운동")
            extra_tags.append(f"{preferred_tool_category} 중심 루틴")

        candidate_pool: List[Tuple[int, Dict[str, Any]]] = []

        for muscle in target_muscles:
            alias_tokens = self._expand_muscle_aliases(muscle)
            prefix = profile_prefix.strip()
            query_variations = self._generate_diverse_queries(
                muscle,
                prefix,
                extra_tags=extra_tags,
                max_variations=6,
            )

            for query in query_variations:
                try:
                    rag_results = self.exercise_rag.search(
                        query,
                        top_k=6,
                        target_group_filter=filters["target_group_filter"],
                        exclude_target_groups=filters["exclude_target_groups"],
                        fitness_factor_filter=filters["fitness_factor_filter"],
                        exclude_fitness_factors=filters["exclude_fitness_factors"],
                    )
                except Exception as exc:
                    print(f"[주간 패턴 분석] ⚠️ Day RAG 검색 실패 (muscle={muscle}, query='{query}'): {exc}")
                    continue

                for item in rag_results:
                    meta = item.get("metadata") or {}
                    exercise_id = meta.get("exercise_id")
                    if exercise_id is None:
                        continue

                    try:
                        normalized_id = int(exercise_id)
                    except (TypeError, ValueError):
                        continue

                    if normalized_id in seen_ids:
                        continue

                    if global_exclude_ids and not allow_reuse and normalized_id in global_exclude_ids:
                        continue

                    if not self._metadata_matches_muscle(meta.get("muscles"), alias_tokens):
                        continue

                    normalized_meta = dict(meta)
                    normalized_meta["exercise_id"] = normalized_id

                    formatted = self._format_rag_exercise_payload(
                        normalized_meta,
                        score=item.get("score"),
                    )
                    seen_ids.add(normalized_id)

                    meta_tool = (meta.get("exercise_tool") or "").strip()
                    meta_tool_category = self._normalize_tool_category(meta_tool)
                    specific_tool_match = False
                    for diary_tool in recent_tools[:5]:
                        if not diary_tool:
                            continue
                        diary_lower = diary_tool.lower()
                        meta_lower = meta_tool.lower()
                        if diary_lower and meta_lower and (
                            diary_lower in meta_lower or meta_lower in diary_lower
                        ):
                            specific_tool_match = True
                            break

                    priority = 2
                    if specific_tool_match:
                        priority = 0
                    elif preferred_tool_category and meta_tool_category == preferred_tool_category:
                        priority = 1

                    candidate_pool.append((priority, formatted))

                if len(day_exercises) >= per_day:
                    break

            if len(day_exercises) >= per_day:
                break

        if candidate_pool:
            candidate_pool.sort(key=lambda entry: entry[0])
            for _, formatted in candidate_pool:
                day_exercises.append(formatted)
                if len(day_exercises) >= per_day:
                    break

        if not day_exercises and global_exclude_ids and not allow_reuse:
            return self._search_day_exercises_with_rag(
                target_muscles,
                profile_data,
                per_day=per_day,
                recent_context=recent_context,
                global_exclude_ids=global_exclude_ids,
                allow_reuse=True,
            )

        return day_exercises

    def _populate_daily_details_with_exercises(
        self,
        daily_details: List[Dict[str, Any]],
        profile_data: Optional[Dict[str, str]],
        fallback_muscles: Optional[List[str]] = None,
        recent_context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[int], List[Dict[str, Any]]]:
        """LLM 루틴 일자에 RAG 운동을 매핑하고 exercise_id 목록과 RAG 정보를 반환"""
        if not daily_details:
            return [], []

        aggregated_ids: List[int] = []
        fallback_validated = validate_and_map_muscles(fallback_muscles or [])
        collected_sources: List[Dict[str, Any]] = []
        global_used_ids: Set[int] = set()

        prepared_items: List[Tuple[Dict[str, Any], List[str]]] = []
        for day in daily_details:
            if not isinstance(day, dict):
                continue

            raw_targets = day.get("target_muscles") or []
            if not isinstance(raw_targets, list):
                raw_targets = []

            validated_targets = validate_and_map_muscles(raw_targets)
            if not validated_targets and fallback_validated:
                validated_targets = fallback_validated[:]

            day["target_muscles"] = validated_targets
            prepared_items.append((day, validated_targets))

        if not self.exercise_rag:
            return aggregated_ids, collected_sources

        for day, targets in prepared_items:
            if not targets:
                day["exercises"] = []
                continue

            day_exercises = self._search_day_exercises_with_rag(
                targets,
                profile_data,
                per_day=4,
                recent_context=recent_context,
                global_exclude_ids=global_used_ids,
            )
            exercise_ids: List[int] = []

            for exercise in day_exercises:
                exercise_id = exercise.get("exercise_id")
                if isinstance(exercise_id, int):
                    aggregated_ids.append(exercise_id)
                    exercise_ids.append(exercise_id)
                    global_used_ids.add(exercise_id)
                collected_sources.append(
                    {
                        "score": exercise.get("score"),
                        "metadata": exercise,
                    }
                )

            day["exercises"] = exercise_ids

        return aggregated_ids, collected_sources

    def _build_muscle_analysis_from_response(
        self, parsed_response: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """LLM 루틴 응답에서 근육 분석 요약을 생성"""
        if not parsed_response:
            return None

        pattern_analysis = parsed_response.get("pattern_analysis", {}) or {}
        muscle_balance = pattern_analysis.get("muscle_balance", {}) or {}

        underworked = muscle_balance.get("underworked") or []
        overworked = muscle_balance.get("overworked") or []
        next_targets = parsed_response.get("next_target_muscles") or []

        validated_under = validate_and_map_muscles(underworked)
        validated_over = validate_and_map_muscles(overworked)
        validated_next = validate_and_map_muscles(next_targets)

        recommendation_focus = (
            pattern_analysis.get("habit_observation")
            or pattern_analysis.get("consistency")
            or pattern_analysis.get("intensity_trend")
            or ""
        )

        return {
            "underworked_muscles": validated_under,
            "overworked_muscles": validated_over,
            "next_target_muscles": validated_next,
            "recommendation_focus": recommendation_focus[:250],
        }

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
            profile_data = self._clean_user_profile(user_profile)
            filters = self._build_rag_filter_options(profile_data)

            return self.exercise_rag.search(
                query, 
                top_k=top_k,
                target_group_filter=filters["target_group_filter"],
                exclude_target_groups=filters["exclude_target_groups"],
                fitness_factor_filter=filters["fitness_factor_filter"],
                exclude_fitness_factors=filters["exclude_fitness_factors"],
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
