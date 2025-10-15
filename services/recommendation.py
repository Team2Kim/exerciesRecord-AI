"""
운동 추천 로직 구현
사용자의 목표와 선호도에 따라 개인화된 운동을 추천합니다.
"""

import random
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from models.database import Exercise, UserGoal, UserFeedback
from models.schemas import RecommendationRequest, RecommendationResponse, DayRecommendation, ExerciseRecommendation
from datetime import datetime


class ExerciseRecommendationService:
    """운동 추천 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # 분할 방식별 운동 부위 매핑
        self.split_mapping = {
            "2분할": {
                "상체": ["가슴", "등", "어깨", "팔"],
                "하체": ["하체", "코어"]
            },
            "3분할": {
                "가슴/삼두": ["가슴", "팔"],
                "등/이두": ["등", "팔"], 
                "하체/어깨": ["하체", "어깨", "코어"]
            },
            "전신": {
                "전신운동": ["가슴", "등", "하체", "어깨", "팔", "코어"]
            }
        }
        
        # 목표별 우선순위 가중치
        self.goal_weights = {
            "근육 증가": {
                "웨이트": 0.7,
                "체중": 0.2,
                "유산소": 0.05,
                "스트레칭": 0.05
            },
            "다이어트": {
                "유산소": 0.4,
                "체중": 0.3,
                "웨이트": 0.2,
                "스트레칭": 0.1
            },
            "체력 향상": {
                "체중": 0.4,
                "유산소": 0.3,
                "웨이트": 0.2,
                "스트레칭": 0.1
            },
            "재활": {
                "스트레칭": 0.4,
                "체중": 0.4,
                "웨이트": 0.1,
                "유산소": 0.1
            }
        }
        
        # 경험 수준별 난이도 필터
        self.difficulty_mapping = {
            "초급": ["초급"],
            "중급": ["초급", "중급"],
            "고급": ["초급", "중급", "고급"]
        }


    def generate_recommendation(self, request: RecommendationRequest) -> RecommendationResponse:
        """메인 추천 생성 함수"""
        try:
            # 1. 사용자 선호도 및 제약 사항 분석
            user_preferences = self._analyze_user_preferences(request)
            
            # 2. 분할 방식에 따른 일별 운동 계획 생성
            daily_plans = self._generate_daily_plans(request, user_preferences)
            
            # 3. 각 일별 운동 추천
            recommendations = {}
            total_weekly_duration = 0
            
            for day_key, day_info in daily_plans.items():
                day_recommendation = self._recommend_exercises_for_day(
                    day_info, request, user_preferences
                )
                recommendations[day_key] = day_recommendation
                total_weekly_duration += day_recommendation.estimated_duration
            
            # 4. 추천 결과 요약 및 팁 생성
            summary = self._generate_summary(request, recommendations, total_weekly_duration)
            tips = self._generate_tips(request, user_preferences)
            difficulty_score = self._calculate_difficulty_score(recommendations)
            
            return RecommendationResponse(
                success=True,
                message="추천이 성공적으로 생성되었습니다.",
                recommendation=recommendations,
                summary=summary,
                tips=tips,
                total_weekly_duration=total_weekly_duration,
                difficulty_score=difficulty_score,
                created_at=datetime.now()
            )
            
        except Exception as e:
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


    def _analyze_user_preferences(self, request: RecommendationRequest) -> Dict[str, Any]:
        """사용자 선호도 분석"""
        preferences = {
            "allowed_difficulties": self.difficulty_mapping[request.experience_level],
            "goal_weights": self.goal_weights.get(request.primary_goal, self.goal_weights["체력 향상"]),
            "excluded_exercises": request.exclude_exercises or [],
            "preferred_equipment": request.preferred_equipment,
            "time_per_session": request.available_time
        }
        
        # 사용자 과거 피드백 분석 (있다면)
        user_feedback = self.db.query(UserFeedback).filter(
            UserFeedback.user_id == request.user_id
        ).all()
        
        if user_feedback:
            # 선호 운동 추출 (평점 4 이상)
            preferred_exercises = [
                fb.exercise_id for fb in user_feedback 
                if fb.rating >= 4
            ]
            
            # 비선호 운동 추출 (평점 2 이하)
            disliked_exercises = [
                fb.exercise_id for fb in user_feedback 
                if fb.rating <= 2
            ]
            
            preferences.update({
                "preferred_exercise_ids": preferred_exercises,
                "disliked_exercise_ids": disliked_exercises
            })
        
        return preferences


    def _generate_daily_plans(self, request: RecommendationRequest, preferences: Dict[str, Any]) -> Dict[str, Dict]:
        """분할 방식에 따른 일별 계획 생성"""
        split_plan = self.split_mapping[request.split_type]
        daily_plans = {}
        
        days_to_generate = min(request.weekly_frequency, len(split_plan))
        
        for i, (day_name, target_parts) in enumerate(split_plan.items()):
            if i >= days_to_generate:
                break
                
            daily_plans[f"Day {i+1}"] = {
                "name": day_name,
                "target_body_parts": target_parts,
                "time_budget": preferences["time_per_session"],
                "warm_up_time": 10,
                "cool_down_time": 10,
                "main_workout_time": preferences["time_per_session"] - 20
            }
        
        return daily_plans


    def _recommend_exercises_for_day(
        self, 
        day_info: Dict[str, Any], 
        request: RecommendationRequest, 
        preferences: Dict[str, Any]
    ) -> DayRecommendation:
        """특정 날짜의 운동 추천"""
        
        target_parts = day_info["target_body_parts"]
        time_budget = day_info["main_workout_time"]
        
        # 해당 부위 운동들 조회
        exercises_query = self.db.query(Exercise).filter(
            Exercise.body_part.in_(target_parts),
            Exercise.difficulty.in_(preferences["allowed_difficulties"]),
            Exercise.target_goal == request.primary_goal
        )
        
        # 제외할 운동 필터링
        if preferences["excluded_exercises"]:
            exercises_query = exercises_query.filter(
                ~Exercise.name.in_(preferences["excluded_exercises"])
            )
        
        # 장비 선호도 반영
        if preferences["preferred_equipment"] and "체중" in preferences["preferred_equipment"]:
            exercises_query = exercises_query.filter(Exercise.category == "체중")
        
        available_exercises = exercises_query.all()
        
        if not available_exercises:
            # 조건이 너무 제한적이면 기본 운동들로 대체
            available_exercises = self.db.query(Exercise).filter(
                Exercise.body_part.in_(target_parts),
                Exercise.difficulty.in_(preferences["allowed_difficulties"])
            ).limit(10).all()
        
        # 운동 선별 및 조합
        selected_exercises = self._select_optimal_exercises(
            available_exercises, target_parts, time_budget, preferences, request
        )
        
        # ExerciseRecommendation 객체로 변환
        exercise_recommendations = []
        total_estimated_time = 0
        
        for exercise, exercise_details in selected_exercises:
            reps_range = self._calculate_reps(exercise, request.primary_goal, request.experience_level)
            sets = self._calculate_sets(exercise, request.experience_level)
            rest_time = self._calculate_rest_time(exercise, request.primary_goal)
            
            recommendation = ExerciseRecommendation(
                name=exercise.name,
                name_en=exercise.name_en,
                body_part=exercise.body_part,
                sets=sets,
                reps=reps_range,
                weight=self._get_weight_guidance(exercise, request.experience_level),
                rest=rest_time,
                instructions=exercise.instructions,
                tips=exercise.tips,
                difficulty=exercise.difficulty,
                equipment=exercise.equipment
            )
            
            exercise_recommendations.append(recommendation)
            total_estimated_time += exercise.duration
        
        return DayRecommendation(
            day_name=day_info["name"],
            target_body_parts=target_parts,
            exercises=exercise_recommendations,
            estimated_duration=total_estimated_time + day_info["warm_up_time"] + day_info["cool_down_time"],
            warm_up_time=day_info["warm_up_time"],
            cool_down_time=day_info["cool_down_time"]
        )


    def _select_optimal_exercises(
        self, 
        exercises: List[Exercise], 
        target_parts: List[str], 
        time_budget: int,
        preferences: Dict[str, Any],
        request: RecommendationRequest
    ) -> List[Tuple[Exercise, Dict]]:
        """최적의 운동 조합 선별"""
        
        # 운동에 점수 부여
        scored_exercises = []
        
        for exercise in exercises:
            score = self._calculate_exercise_score(exercise, target_parts, preferences, request)
            scored_exercises.append((exercise, score))
        
        # 점수 순으로 정렬
        scored_exercises.sort(key=lambda x: x[1], reverse=True)
        
        # 시간과 부위 균형을 고려해서 선별
        selected = []
        used_time = 0
        part_coverage = {part: 0 for part in target_parts}
        
        # 부위별로 최소 1개씩 선택
        for part in target_parts:
            for exercise, score in scored_exercises:
                if (exercise.body_part == part and 
                    used_time + exercise.duration <= time_budget and
                    exercise not in [ex[0] for ex in selected]):
                    
                    selected.append((exercise, {"score": score, "priority": "primary"}))
                    used_time += exercise.duration
                    part_coverage[part] += 1
                    break
        
        # 남은 시간에 추가 운동 배치
        for exercise, score in scored_exercises:
            if (exercise not in [ex[0] for ex in selected] and 
                used_time + exercise.duration <= time_budget):
                
                selected.append((exercise, {"score": score, "priority": "secondary"}))
                used_time += exercise.duration
                
                # 시간 예산의 80% 정도 사용하면 중단
                if used_time >= time_budget * 0.8:
                    break
        
        return selected


    def _calculate_exercise_score(
        self, 
        exercise: Exercise, 
        target_parts: List[str], 
        preferences: Dict[str, Any],
        request: RecommendationRequest
    ) -> float:
        """운동별 점수 계산"""
        score = 0.0
        
        # 1. 부위 일치도 (30%)
        if exercise.body_part in target_parts:
            score += 0.3
        
        # 2. 목표 일치도 (25%)  
        if exercise.target_goal == request.primary_goal:
            score += 0.25
        
        # 3. 카테고리 가중치 (20%)
        category_weight = preferences["goal_weights"].get(exercise.category, 0.1)
        score += category_weight * 0.2
        
        # 4. 사용자 피드백 반영 (15%)
        if "preferred_exercise_ids" in preferences:
            if exercise.id in preferences["preferred_exercise_ids"]:
                score += 0.15
            elif exercise.id in preferences.get("disliked_exercise_ids", []):
                score -= 0.1
        
        # 5. 시간 효율성 (10%)
        if exercise.duration <= 30:  # 30분 이하면 효율적
            score += 0.1
        elif exercise.duration > 60:  # 60분 초과면 비효율적
            score -= 0.05
        
        # 6. 랜덤 요소 (다양성 확보)
        score += random.random() * 0.1
        
        return score


    def _calculate_reps(self, exercise: Exercise, goal: str, level: str) -> str:
        """반복 횟수 계산"""
        base_reps = {
            "근육 증가": {
                "초급": "8-12",
                "중급": "8-12", 
                "고급": "6-12"
            },
            "다이어트": {
                "초급": "12-15",
                "중급": "12-18",
                "고급": "15-20"
            },
            "체력 향상": {
                "초급": "10-15",
                "중급": "12-18", 
                "고급": "15-25"
            }
        }
        
        if exercise.category == "유산소":
            return f"{exercise.duration}분"
        elif exercise.category == "스트레칭":
            return f"{exercise.duration}초 유지"
        
        return base_reps.get(goal, {}).get(level, "10-15")


    def _calculate_sets(self, exercise: Exercise, level: str) -> int:
        """세트 수 계산"""
        if exercise.category in ["유산소", "스트레칭"]:
            return 1
            
        set_mapping = {
            "초급": 3,
            "중급": 3,
            "고급": 4
        }
        
        return set_mapping.get(level, 3)


    def _calculate_rest_time(self, exercise: Exercise, goal: str) -> str:
        """휴식 시간 계산"""
        if exercise.category == "유산소":
            return "없음"
        elif exercise.category == "스트레칭":
            return "10초"
        
        rest_mapping = {
            "근육 증가": "2-3분",
            "다이어트": "1-2분",
            "체력 향상": "1-2분"
        }
        
        return rest_mapping.get(goal, "2분")


    def _get_weight_guidance(self, exercise: Exercise, level: str) -> str:
        """무게 가이드 제공"""
        if exercise.category != "웨이트":
            return None
            
        weight_guidance = {
            "초급": "가벼운 무게부터 시작",
            "중급": "1RM의 70-80%",
            "고급": "1RM의 75-85%"
        }
        
        return weight_guidance.get(level, "적절한 무게")


    def _generate_summary(
        self, 
        request: RecommendationRequest, 
        recommendations: Dict[str, DayRecommendation],
        total_duration: int
    ) -> Dict[str, Any]:
        """추천 결과 요약 생성"""
        
        total_exercises = sum(len(day.exercises) for day in recommendations.values())
        
        # 부위별 운동 분포
        body_part_count = {}
        category_count = {}
        
        for day in recommendations.values():
            for exercise in day.exercises:
                body_part_count[exercise.body_part] = body_part_count.get(exercise.body_part, 0) + 1
                category = "웨이트" if exercise.equipment else "체중"
                category_count[category] = category_count.get(category, 0) + 1
        
        return {
            "total_days": len(recommendations),
            "total_exercises": total_exercises,
            "total_weekly_duration": total_duration,
            "avg_session_duration": total_duration // len(recommendations) if recommendations else 0,
            "body_part_distribution": body_part_count,
            "category_distribution": category_count,
            "split_type": request.split_type,
            "primary_goal": request.primary_goal,
            "experience_level": request.experience_level
        }


    def _generate_tips(self, request: RecommendationRequest, preferences: Dict[str, Any]) -> List[str]:
        """맞춤 팁 생성"""
        tips = []
        
        # 경험 수준별 팁
        if request.experience_level == "초급":
            tips.extend([
                "처음에는 정확한 자세가 가장 중요합니다. 무게보다 폼에 집중하세요.",
                "운동 전후 충분한 워밍업과 쿨다운을 실시하세요.",
                "몸의 신호를 잘 들어보고 무리하지 마세요."
            ])
        elif request.experience_level == "고급":
            tips.extend([
                "고급자는 점진적 과부하와 운동 변화를 통해 발전을 이어가세요.",
                "부상 예방을 위해 모빌리티와 회복에도 신경 쓰세요."
            ])
        
        # 목표별 팁
        if request.primary_goal == "근육 증가":
            tips.extend([
                "근육 성장을 위해 충분한 단백질 섭취와 휴식이 중요합니다.",
                "복합 운동을 우선적으로 수행하고, 고립 운동으로 보완하세요."
            ])
        elif request.primary_goal == "다이어트":
            tips.extend([
                "유산소와 근력 운동을 병행하여 효과적인 칼로리 소모를 하세요.",
                "운동과 함께 식단 관리를 병행하면 더욱 효과적입니다."
            ])
        
        # 시간 관련 팁
        if request.available_time < 45:
            tips.append("짧은 시간이지만 고강도로 집중해서 운동하세요.")
        elif request.available_time > 90:
            tips.append("충분한 시간이 있으니 워밍업과 쿨다운을 철저히 하세요.")
        
        return tips[:5]  # 최대 5개 팁만 반환


    def _calculate_difficulty_score(self, recommendations: Dict[str, DayRecommendation]) -> float:
        """전체 운동 난이도 점수 계산 (1-5)"""
        difficulty_scores = {
            "초급": 1,
            "중급": 3,
            "고급": 5
        }
        
        total_score = 0
        total_exercises = 0
        
        for day in recommendations.values():
            for exercise in day.exercises:
                total_score += difficulty_scores.get(exercise.difficulty, 3)
                total_exercises += 1
        
        if total_exercises == 0:
            return 3.0
            
        return round(total_score / total_exercises, 1)

