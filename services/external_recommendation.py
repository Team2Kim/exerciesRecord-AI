"""
외부 API 데이터 기반 운동 추천 서비스
외부 운동 영상 API에서 받아온 데이터를 활용해서 추천을 생성합니다.
"""

import random
from typing import List, Dict, Any, Optional
from services.external_api import external_api
from models.schemas import RecommendationRequest, RecommendationResponse, DayRecommendation, ExerciseRecommendation
from datetime import datetime


class ExternalAPIRecommendationService:
    """외부 API 데이터 기반 추천 서비스"""
    
    def __init__(self):
        # 분할 방식별 운동 부위 매핑 (외부 API 키워드에 맞춤)
        self.split_mapping = {
            "2분할": {
                "상체운동": ["상체", "가슴", "등", "어깨", "팔"],
                "하체운동": ["하체", "다리", "허벅지", "종아리"]
            },
            "3분할": {
                "가슴/삼두": ["가슴", "삼두", "팔굽혀펴기"],
                "등/이두": ["등", "이두", "풀업", "턱걸이"],
                "하체/어깨": ["하체", "어깨", "스쿼트", "런지"]
            },
            "전신": {
                "전신운동": ["전신", "복합운동", "기능성", "체중"]
            }
        }
        
        # 목표별 운동 키워드 매핑
        self.goal_keywords = {
            "근육 증가": ["근력", "웨이트", "덤벨", "바벨"],
            "다이어트": ["유산소", "칼로리", "다이어트", "체중감량"],
            "체력 향상": ["체력", "지구력", "기능성", "맨몸"],
            "재활": ["재활", "스트레칭", "가동성", "회복"]
        }
        
        # 경험 수준별 필터
        self.experience_mapping = {
            "초급": "유소년",
            "중급": "청소년", 
            "고급": "성인"
        }


    async def generate_external_recommendation(self, request: RecommendationRequest) -> RecommendationResponse:
        """외부 API 데이터를 기반으로 추천 생성"""
        try:
            print(f"🔥 외부 API 기반 추천 시작 - 사용자: {request.user_id}")
            
            # 1. 사용자 프로필 분석
            user_profile = self._analyze_user_profile(request)
            
            # 2. 외부 API에서 운동 데이터 수집
            exercise_pool = await self._collect_exercise_data(user_profile, request)
            
            if not exercise_pool:
                return RecommendationResponse(
                    success=False,
                    message="외부 API에서 적합한 운동을 찾을 수 없습니다.",
                    recommendation={},
                    summary={},
                    tips=[],
                    total_weekly_duration=0,
                    difficulty_score=0.0,
                    created_at=datetime.now()
                )
            
            # 3. 분할 방식에 따른 일별 계획 생성
            daily_plans = self._generate_daily_plans(request, exercise_pool)
            
            # 4. 각 일별 운동 추천 생성
            recommendations = {}
            total_weekly_duration = 0
            
            for day_key, day_data in daily_plans.items():
                day_recommendation = await self._create_day_recommendation(
                    day_key, day_data, request, exercise_pool
                )
                recommendations[day_key] = day_recommendation
                total_weekly_duration += day_recommendation.estimated_duration
            
            # 5. 요약 및 팁 생성
            summary = self._generate_summary(request, recommendations, total_weekly_duration)
            tips = self._generate_tips(request, exercise_pool)
            difficulty_score = self._calculate_difficulty_score(exercise_pool, request.experience_level)
            
            return RecommendationResponse(
                success=True,
                message="외부 API 데이터 기반 추천이 성공적으로 생성되었습니다.",
                recommendation=recommendations,
                summary=summary,
                tips=tips,
                total_weekly_duration=total_weekly_duration,
                difficulty_score=difficulty_score,
                created_at=datetime.now()
            )
            
        except Exception as e:
            print(f"❌ 외부 API 추천 생성 오류: {e}")
            return RecommendationResponse(
                success=False,
                message=f"추천 생성 중 오류가 발생했습니다: {str(e)}",
                recommendation={},
                summary={},
                tips=[],
                total_weekly_duration=0,
                difficulty_score=0.0,
                created_at=datetime.now()
            )


    def _analyze_user_profile(self, request: RecommendationRequest) -> Dict[str, Any]:
        """사용자 프로필 분석"""
        target_group = self.experience_mapping.get(request.experience_level, "성인")
        goal_keywords = self.goal_keywords.get(request.primary_goal, ["기본"])
        
        return {
            "target_group": target_group,
            "goal_keywords": goal_keywords,
            "available_time": request.available_time,
            "weekly_frequency": request.weekly_frequency,
            "split_type": request.split_type,
            "preferred_equipment": request.preferred_equipment
        }


    async def _collect_exercise_data(self, user_profile: Dict, request: RecommendationRequest) -> List[Dict]:
        """외부 API에서 운동 데이터 수집"""
        exercise_pool = []
        
        # 분할 방식에 따른 부위별 검색
        split_plan = self.split_mapping[request.split_type]
        
        for day_name, body_parts in split_plan.items():
            for body_part in body_parts:
                # 각 부위별로 운동 검색
                for goal_keyword in user_profile["goal_keywords"]:
                    try:
                        result = await external_api.search_exercises(
                            keyword=f"{body_part} {goal_keyword}",
                            target_group=user_profile["target_group"],
                            size=5
                        )
                        
                        if result.get("content"):
                            for exercise in result["content"]:
                                # 운동 데이터에 추가 정보 태깅
                                exercise["recommended_body_part"] = body_part
                                exercise["day_assignment"] = day_name
                                exercise["goal_match"] = goal_keyword
                                exercise_pool.append(exercise)
                        
                    except Exception as e:
                        print(f"⚠️ 검색 오류 ({body_part} {goal_keyword}): {e}")
                        continue
        
        # 중복 제거 (exerciseId 기준)
        unique_exercises = {}
        for exercise in exercise_pool:
            exercise_id = exercise.get("exerciseId")
            if exercise_id and exercise_id not in unique_exercises:
                unique_exercises[exercise_id] = exercise
        
        return list(unique_exercises.values())


    def _generate_daily_plans(self, request: RecommendationRequest, exercise_pool: List[Dict]) -> Dict[str, Dict]:
        """일별 운동 계획 생성"""
        split_plan = self.split_mapping[request.split_type]
        daily_plans = {}
        
        days_to_generate = min(request.weekly_frequency, len(split_plan))
        
        for i, (day_name, body_parts) in enumerate(split_plan.items()):
            if i >= days_to_generate:
                break
                
            # 해당 날짜에 배정된 운동들 필터링
            day_exercises = [
                ex for ex in exercise_pool 
                if ex.get("day_assignment") == day_name
            ]
            
            daily_plans[f"Day {i+1}"] = {
                "name": day_name,
                "target_body_parts": body_parts,
                "available_exercises": day_exercises,
                "time_budget": request.available_time - 20,  # 워밍업/쿨다운 시간 제외
                "warm_up_time": 10,
                "cool_down_time": 10
            }
        
        return daily_plans


    async def _create_day_recommendation(
        self, 
        day_key: str, 
        day_data: Dict, 
        request: RecommendationRequest, 
        exercise_pool: List[Dict]
    ) -> DayRecommendation:
        """일별 추천 운동 생성"""
        
        available_exercises = day_data["available_exercises"]
        target_parts = day_data["target_body_parts"]
        time_budget = day_data["time_budget"]
        
        # 운동이 부족하면 추가로 검색
        if len(available_exercises) < 3:
            for part in target_parts[:2]:  # 최대 2개 부위만 추가 검색
                try:
                    additional_result = await external_api.search_exercises(
                        keyword=part,
                        target_group=self.experience_mapping.get(request.experience_level, "성인"),
                        size=3
                    )
                    
                    if additional_result.get("content"):
                        available_exercises.extend(additional_result["content"])
                        
                except Exception as e:
                    print(f"⚠️ 추가 검색 오류: {e}")
        
        # 운동 선별 및 추천 생성
        selected_exercises = self._select_best_exercises(
            available_exercises, target_parts, time_budget, request
        )
        
        exercise_recommendations = []
        total_time = day_data["warm_up_time"] + day_data["cool_down_time"]
        
        for exercise_data in selected_exercises:
            # 외부 API 데이터를 ExerciseRecommendation 형태로 변환
            recommendation = self._convert_to_exercise_recommendation(exercise_data, request)
            exercise_recommendations.append(recommendation)
            
            # 예상 시간 계산 (영상 길이 기준, 없으면 기본값)
            duration = exercise_data.get("videoLengthSeconds", 180) // 60  # 초를 분으로 변환
            total_time += max(duration, 5)  # 최소 5분
        
        return DayRecommendation(
            day_name=day_data["name"],
            target_body_parts=target_parts,
            exercises=exercise_recommendations,
            estimated_duration=min(total_time, request.available_time),
            warm_up_time=day_data["warm_up_time"],
            cool_down_time=day_data["cool_down_time"]
        )


    def _select_best_exercises(
        self, 
        exercises: List[Dict], 
        target_parts: List[str], 
        time_budget: int,
        request: RecommendationRequest
    ) -> List[Dict]:
        """최적의 운동 선별"""
        
        if not exercises:
            return []
        
        # 운동에 점수 부여
        scored_exercises = []
        for exercise in exercises:
            score = self._calculate_exercise_score(exercise, target_parts, request)
            scored_exercises.append((exercise, score))
        
        # 점수 순으로 정렬
        scored_exercises.sort(key=lambda x: x[1], reverse=True)
        
        # 시간 예산 내에서 선별
        selected = []
        used_time = 0
        max_exercises = min(6, len(scored_exercises))  # 최대 6개 운동
        
        for exercise, score in scored_exercises[:max_exercises]:
            # 영상 길이 확인 (초 -> 분 변환)
            duration = exercise.get("videoLengthSeconds", 180) // 60
            duration = max(duration, 3)  # 최소 3분
            
            if used_time + duration <= time_budget:
                selected.append(exercise)
                used_time += duration
                
                # 충분한 운동이 선별되면 중단
                if len(selected) >= 4 or used_time >= time_budget * 0.8:
                    break
        
        return selected


    def _calculate_exercise_score(self, exercise: Dict, target_parts: List[str], request: RecommendationRequest) -> float:
        """운동 점수 계산"""
        score = 0.0
        
        # 1. 제목 관련성 (30%)
        title = exercise.get("title", "").lower()
        for part in target_parts:
            if part.lower() in title:
                score += 0.3
                break
        
        # 2. 목표 일치도 (25%)
        goal_keywords = self.goal_keywords.get(request.primary_goal, [])
        for keyword in goal_keywords:
            if keyword.lower() in title:
                score += 0.25
                break
        
        # 3. 대상 그룹 일치도 (20%)
        target_group = exercise.get("targetGroup", "")
        expected_group = self.experience_mapping.get(request.experience_level, "성인")
        if target_group == expected_group:
            score += 0.2
        
        # 4. 영상 품질 (15%)
        video_length = exercise.get("videoLengthSeconds", 0)
        if 60 <= video_length <= 1800:  # 1분~30분 영상 선호
            score += 0.15
        elif video_length > 0:
            score += 0.05
        
        # 5. 장비 선호도 (10%)
        if request.preferred_equipment:
            exercise_tool = exercise.get("exerciseTool", "")
            if request.preferred_equipment.lower() in exercise_tool.lower():
                score += 0.1
        
        # 6. 랜덤 요소 (다양성)
        score += random.random() * 0.1
        
        return score


    def _convert_to_exercise_recommendation(self, exercise_data: Dict, request: RecommendationRequest) -> ExerciseRecommendation:
        """외부 API 데이터를 ExerciseRecommendation으로 변환"""
        
        # 기본값 설정
        sets = self._calculate_sets_for_goal(request.primary_goal, request.experience_level)
        reps = self._calculate_reps_for_goal(request.primary_goal, request.experience_level)
        rest = self._calculate_rest_for_goal(request.primary_goal)
        
        return ExerciseRecommendation(
            name=exercise_data.get("title", "운동"),
            name_en=None,
            body_part=exercise_data.get("targetGroup", "전신"),
            sets=sets,
            reps=reps,
            weight=self._get_weight_guidance(request.experience_level),
            rest=rest,
            instructions=exercise_data.get("description"),
            tips=f"영상 시청을 통해 정확한 자세를 학습하세요. 영상 길이: {exercise_data.get('videoLengthSeconds', 0)//60}분",
            difficulty=request.experience_level,
            equipment=exercise_data.get("exerciseTool"),
            video_url=exercise_data.get("videoUrl"),
            video_id=exercise_data.get("exerciseId"),
            image_url=exercise_data.get("imageUrl"),
            video_length=exercise_data.get("videoLengthSeconds"),
            target_group=exercise_data.get("targetGroup"),
            fitness_factor=exercise_data.get("fitnessFactorName")
        )


    def _calculate_sets_for_goal(self, goal: str, level: str) -> int:
        """목표와 수준에 따른 세트 수 계산"""
        base_sets = {
            "근육 증가": {"초급": 3, "중급": 4, "고급": 4},
            "다이어트": {"초급": 3, "중급": 3, "고급": 4},
            "체력 향상": {"초급": 2, "중급": 3, "고급": 3},
            "재활": {"초급": 2, "중급": 2, "고급": 3}
        }
        return base_sets.get(goal, {}).get(level, 3)


    def _calculate_reps_for_goal(self, goal: str, level: str) -> str:
        """목표와 수준에 따른 반복 횟수 계산"""
        base_reps = {
            "근육 증가": {"초급": "8-12", "중급": "8-12", "고급": "6-12"},
            "다이어트": {"초급": "12-15", "중급": "15-20", "고급": "15-25"},
            "체력 향상": {"초급": "10-15", "중급": "12-20", "고급": "15-25"},
            "재활": {"초급": "8-10", "중급": "10-12", "고급": "12-15"}
        }
        return base_reps.get(goal, {}).get(level, "10-15")


    def _calculate_rest_for_goal(self, goal: str) -> str:
        """목표에 따른 휴식 시간 계산"""
        rest_times = {
            "근육 증가": "2-3분",
            "다이어트": "1-2분",
            "체력 향상": "1-2분", 
            "재활": "2-3분"
        }
        return rest_times.get(goal, "2분")


    def _get_weight_guidance(self, level: str) -> Optional[str]:
        """수준에 따른 무게 가이드"""
        guidance = {
            "초급": "가벼운 무게로 시작하여 점진적으로 증가",
            "중급": "적절한 강도로 도전적인 무게 사용",
            "고급": "고강도 훈련으로 한계에 도전"
        }
        return guidance.get(level)


    def _generate_summary(self, request: RecommendationRequest, recommendations: Dict, total_duration: int) -> Dict[str, Any]:
        """요약 정보 생성"""
        total_exercises = sum(len(day.exercises) for day in recommendations.values())
        
        return {
            "total_days": len(recommendations),
            "total_exercises": total_exercises,
            "total_weekly_duration": total_duration,
            "avg_session_duration": total_duration // len(recommendations) if recommendations else 0,
            "data_source": "external_api",
            "split_type": request.split_type,
            "primary_goal": request.primary_goal,
            "experience_level": request.experience_level,
            "api_based": True
        }


    def _generate_tips(self, request: RecommendationRequest, exercise_pool: List[Dict]) -> List[str]:
        """맞춤 팁 생성"""
        tips = [
            "실제 운동 영상을 통해 정확한 자세를 학습하세요.",
            "각 운동의 영상을 먼저 시청한 후 실시하는 것을 권장합니다."
        ]
        
        # 경험 수준별 팁
        if request.experience_level == "초급":
            tips.extend([
                "처음에는 영상을 천천히 보면서 동작을 익혀보세요.",
                "무리하지 말고 본인의 체력에 맞게 조절하세요."
            ])
        elif request.experience_level == "고급":
            tips.append("다양한 운동 변형을 통해 새로운 자극을 경험해보세요.")
        
        # 목표별 팁
        if request.primary_goal == "근육 증가":
            tips.append("영상에서 근육의 수축과 이완에 집중하는 포인트를 확인하세요.")
        elif request.primary_goal == "다이어트":
            tips.append("고강도 운동 영상을 활용하여 더 많은 칼로리를 소모하세요.")
        
        return tips[:6]  # 최대 6개 팁


    def _calculate_difficulty_score(self, exercise_pool: List[Dict], experience_level: str) -> float:
        """난이도 점수 계산"""
        base_scores = {"초급": 2.0, "중급": 3.5, "고급": 4.5}
        base_score = base_scores.get(experience_level, 3.0)
        
        # 운동 영상 수에 따른 조정
        if len(exercise_pool) > 20:
            return min(base_score + 0.5, 5.0)
        elif len(exercise_pool) < 10:
            return max(base_score - 0.5, 1.0)
        
        return base_score


# 전역 인스턴스
external_recommendation_service = ExternalAPIRecommendationService()

