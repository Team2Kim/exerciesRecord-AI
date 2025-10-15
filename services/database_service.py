"""
데이터베이스 서비스 레이어
비즈니스 로직과 데이터베이스 접근을 분리합니다.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from models.database import Exercise, UserGoal, WorkoutPlan, WorkoutSession, WorkoutExercise, UserFeedback, DailyLog, LogExercise
from models.schemas import (
    ExerciseCreate, UserGoalCreate, WorkoutPlanCreate, 
    UserFeedbackCreate, RecommendationRequest,
    DailyLogCreate, DailyLogUpdate, LogExerciseCreate, LogExerciseUpdate
)


class DatabaseService:
    """데이터베이스 서비스 클래스"""
    
    def __init__(self, db: Session):
        self.db = db


    # ==================== Exercise 관련 ====================
    def get_exercises(
        self, 
        skip: int = 0, 
        limit: int = 100,
        body_part: Optional[str] = None,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        target_goal: Optional[str] = None
    ) -> List[Exercise]:
        """운동 목록 조회 (필터링 포함)"""
        query = self.db.query(Exercise)
        
        # 필터 적용
        if body_part:
            query = query.filter(Exercise.body_part == body_part)
        if category:
            query = query.filter(Exercise.category == category)
        if difficulty:
            query = query.filter(Exercise.difficulty == difficulty)
        if target_goal:
            query = query.filter(Exercise.target_goal == target_goal)
        
        return query.offset(skip).limit(limit).all()


    def get_exercise_by_id(self, exercise_id: int) -> Optional[Exercise]:
        """ID로 운동 조회"""
        return self.db.query(Exercise).filter(Exercise.id == exercise_id).first()


    def search_exercises(self, search_term: str, limit: int = 50) -> List[Exercise]:
        """운동 검색"""
        return self.db.query(Exercise).filter(
            or_(
                Exercise.name.contains(search_term),
                Exercise.name_en.contains(search_term),
                Exercise.muscle_group.contains(search_term),
                Exercise.instructions.contains(search_term)
            )
        ).limit(limit).all()


    def create_exercise(self, exercise_data: ExerciseCreate) -> Exercise:
        """새 운동 생성"""
        db_exercise = Exercise(**exercise_data.dict())
        self.db.add(db_exercise)
        self.db.commit()
        self.db.refresh(db_exercise)
        return db_exercise


    def get_exercises_by_body_parts(self, body_parts: List[str]) -> List[Exercise]:
        """특정 부위들의 운동 조회"""
        return self.db.query(Exercise).filter(Exercise.body_part.in_(body_parts)).all()


    def get_popular_exercises(self, limit: int = 10) -> List[Exercise]:
        """인기 운동 조회 (피드백 기준)"""
        popular_exercises = self.db.query(
            Exercise,
            func.avg(UserFeedback.rating).label('avg_rating'),
            func.count(UserFeedback.id).label('feedback_count')
        ).join(
            UserFeedback, Exercise.id == UserFeedback.exercise_id
        ).group_by(
            Exercise.id
        ).having(
            func.count(UserFeedback.id) >= 3  # 최소 3개 이상의 피드백
        ).order_by(
            func.avg(UserFeedback.rating).desc()
        ).limit(limit).all()
        
        return [result[0] for result in popular_exercises]


    # ==================== UserGoal 관련 ====================
    def create_user_goal(self, goal_data: UserGoalCreate) -> UserGoal:
        """사용자 목표 생성"""
        db_goal = UserGoal(**goal_data.dict())
        self.db.add(db_goal)
        self.db.commit()
        self.db.refresh(db_goal)
        return db_goal


    def get_user_goal(self, user_id: str) -> Optional[UserGoal]:
        """사용자의 최신 목표 조회"""
        return self.db.query(UserGoal).filter(
            UserGoal.user_id == user_id
        ).order_by(UserGoal.created_at.desc()).first()


    def get_user_goals_history(self, user_id: str) -> List[UserGoal]:
        """사용자 목표 히스토리 조회"""
        return self.db.query(UserGoal).filter(
            UserGoal.user_id == user_id
        ).order_by(UserGoal.created_at.desc()).all()


    def update_user_goal(self, goal_id: int, **updates) -> Optional[UserGoal]:
        """사용자 목표 업데이트"""
        goal = self.db.query(UserGoal).filter(UserGoal.id == goal_id).first()
        if goal:
            for key, value in updates.items():
                if hasattr(goal, key) and value is not None:
                    setattr(goal, key, value)
            self.db.commit()
            self.db.refresh(goal)
        return goal


    # ==================== WorkoutPlan 관련 ====================
    def create_workout_plan(self, plan_data: WorkoutPlanCreate) -> WorkoutPlan:
        """운동 계획 생성"""
        db_plan = WorkoutPlan(
            user_goal_id=plan_data.user_goal_id,
            plan_name=plan_data.plan_name,
            total_duration=plan_data.total_duration,
            difficulty_score=plan_data.difficulty_score
        )
        self.db.add(db_plan)
        self.db.commit()
        self.db.refresh(db_plan)
        return db_plan


    def get_workout_plans(self, user_id: str, limit: int = 10) -> List[WorkoutPlan]:
        """사용자의 운동 계획들 조회"""
        return self.db.query(WorkoutPlan).join(UserGoal).filter(
            UserGoal.user_id == user_id
        ).order_by(WorkoutPlan.created_at.desc()).limit(limit).all()


    def get_workout_plan_by_id(self, plan_id: int) -> Optional[WorkoutPlan]:
        """ID로 운동 계획 조회"""
        return self.db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()


    # ==================== UserFeedback 관련 ====================
    def create_feedback(self, feedback_data: UserFeedbackCreate) -> UserFeedback:
        """피드백 생성"""
        db_feedback = UserFeedback(**feedback_data.dict())
        self.db.add(db_feedback)
        self.db.commit()
        self.db.refresh(db_feedback)
        return db_feedback


    def get_user_feedback(self, user_id: str, exercise_id: Optional[int] = None) -> List[UserFeedback]:
        """사용자 피드백 조회"""
        query = self.db.query(UserFeedback).filter(UserFeedback.user_id == user_id)
        
        if exercise_id:
            query = query.filter(UserFeedback.exercise_id == exercise_id)
            
        return query.order_by(UserFeedback.created_at.desc()).all()


    def get_exercise_feedback_summary(self, exercise_id: int) -> Dict[str, Any]:
        """운동별 피드백 요약"""
        feedback_stats = self.db.query(
            func.count(UserFeedback.id).label('total_feedback'),
            func.avg(UserFeedback.rating).label('avg_rating'),
            func.avg(UserFeedback.difficulty_rating).label('avg_difficulty'),
            func.avg(UserFeedback.enjoyment_rating).label('avg_enjoyment'),
            func.avg(UserFeedback.effectiveness_rating).label('avg_effectiveness')
        ).filter(UserFeedback.exercise_id == exercise_id).first()
        
        return {
            'total_feedback': feedback_stats.total_feedback or 0,
            'avg_rating': round(feedback_stats.avg_rating or 0, 1),
            'avg_difficulty': round(feedback_stats.avg_difficulty or 0, 1),
            'avg_enjoyment': round(feedback_stats.avg_enjoyment or 0, 1),
            'avg_effectiveness': round(feedback_stats.avg_effectiveness or 0, 1)
        }


    # ==================== 통계 및 분석 관련 ====================
    def get_database_stats(self) -> Dict[str, Any]:
        """데이터베이스 통계 조회"""
        exercise_count = self.db.query(Exercise).count()
        user_goal_count = self.db.query(UserGoal).count()
        plan_count = self.db.query(WorkoutPlan).count()
        feedback_count = self.db.query(UserFeedback).count()
        
        # 부위별 운동 분포
        body_part_stats = self.db.query(
            Exercise.body_part,
            func.count(Exercise.id).label('count')
        ).group_by(Exercise.body_part).all()
        
        # 카테고리별 운동 분포
        category_stats = self.db.query(
            Exercise.category,
            func.count(Exercise.id).label('count')
        ).group_by(Exercise.category).all()
        
        # 목표별 사용자 분포
        goal_stats = self.db.query(
            UserGoal.primary_goal,
            func.count(UserGoal.id).label('count')
        ).group_by(UserGoal.primary_goal).all()
        
        return {
            'total_exercises': exercise_count,
            'total_users': user_goal_count,
            'total_plans': plan_count,
            'total_feedback': feedback_count,
            'body_part_distribution': {stat.body_part: stat.count for stat in body_part_stats},
            'category_distribution': {stat.category: stat.count for stat in category_stats},
            'goal_distribution': {stat.primary_goal: stat.count for stat in goal_stats}
        }


    def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """사용자 분석 데이터"""
        user_goals = self.get_user_goals_history(user_id)
        user_feedback = self.get_user_feedback(user_id)
        user_plans = self.get_workout_plans(user_id)
        
        if not user_goals:
            return {}
        
        latest_goal = user_goals[0]
        
        # 피드백 통계
        feedback_stats = {
            'total_feedback': len(user_feedback),
            'avg_rating': sum(fb.rating for fb in user_feedback) / len(user_feedback) if user_feedback else 0,
            'preferred_exercises': [fb.exercise_id for fb in user_feedback if fb.rating >= 4],
            'disliked_exercises': [fb.exercise_id for fb in user_feedback if fb.rating <= 2]
        }
        
        # 선호하는 운동 부위 분석
        if user_feedback:
            exercise_ids = [fb.exercise_id for fb in user_feedback if fb.rating >= 4]
            if exercise_ids:
                preferred_parts = self.db.query(
                    Exercise.body_part,
                    func.count(Exercise.id).label('count')
                ).filter(
                    Exercise.id.in_(exercise_ids)
                ).group_by(Exercise.body_part).all()
                
                feedback_stats['preferred_body_parts'] = {
                    part.body_part: part.count for part in preferred_parts
                }
        
        return {
            'user_id': user_id,
            'latest_goal': {
                'primary_goal': latest_goal.primary_goal,
                'split_type': latest_goal.split_type,
                'weekly_frequency': latest_goal.weekly_frequency,
                'experience_level': latest_goal.experience_level,
                'available_time': latest_goal.available_time
            },
            'total_plans_created': len(user_plans),
            'feedback_stats': feedback_stats,
            'goal_history_count': len(user_goals)
        }


    # ==================== 추천 관련 헬퍼 메소드 ====================
    def get_exercises_for_recommendation(self, request: RecommendationRequest) -> List[Exercise]:
        """추천을 위한 운동 데이터 조회"""
        query = self.db.query(Exercise)
        
        # 기본 필터: 목표에 맞는 운동
        query = query.filter(Exercise.target_goal == request.primary_goal)
        
        # 경험 수준에 따른 난이도 필터
        difficulty_mapping = {
            "초급": ["초급"],
            "중급": ["초급", "중급"],
            "고급": ["초급", "중급", "고급"]
        }
        allowed_difficulties = difficulty_mapping.get(request.experience_level, ["초급", "중급"])
        query = query.filter(Exercise.difficulty.in_(allowed_difficulties))
        
        # 제외할 운동이 있다면 필터링
        if request.exclude_exercises:
            query = query.filter(~Exercise.name.in_(request.exclude_exercises))
        
        # 시간 제한 고려 (너무 오래 걸리는 운동 제외)
        max_duration = min(request.available_time // 2, 60)  # 전체 시간의 절반 이하, 최대 60분
        query = query.filter(Exercise.duration <= max_duration)
        
        return query.all()


    def save_recommendation_as_plan(
        self, 
        user_id: str, 
        recommendation_data: Dict[str, Any],
        plan_name: str = "AI 추천 계획"
    ) -> Optional[WorkoutPlan]:
        """추천 결과를 운동 계획으로 저장"""
        try:
            # 사용자 목표 조회
            user_goal = self.get_user_goal(user_id)
            if not user_goal:
                return None
            
            # 운동 계획 생성
            total_duration = recommendation_data.get('total_weekly_duration', 0)
            difficulty_score = recommendation_data.get('difficulty_score', 3.0)
            
            workout_plan = WorkoutPlan(
                user_goal_id=user_goal.id,
                plan_name=plan_name,
                total_duration=total_duration,
                difficulty_score=difficulty_score
            )
            
            self.db.add(workout_plan)
            self.db.commit()
            self.db.refresh(workout_plan)
            
            # 세션별 운동 저장
            recommendations = recommendation_data.get('recommendation', {})
            for day_key, day_data in recommendations.items():
                # 운동 세션 생성
                session = WorkoutSession(
                    workout_plan_id=workout_plan.id,
                    day_number=int(day_key.split(' ')[1]),  # "Day 1" -> 1
                    day_name=day_data.day_name,
                    target_body_parts=','.join(day_data.target_body_parts),
                    estimated_duration=day_data.estimated_duration
                )
                
                self.db.add(session)
                self.db.commit()
                self.db.refresh(session)
                
                # 개별 운동 저장
                for idx, exercise_rec in enumerate(day_data.exercises):
                    # 운동 이름으로 ID 찾기
                    exercise = self.db.query(Exercise).filter(
                        Exercise.name == exercise_rec.name
                    ).first()
                    
                    if exercise:
                        workout_exercise = WorkoutExercise(
                            workout_session_id=session.id,
                            exercise_id=exercise.id,
                            order_in_session=idx + 1,
                            sets=exercise_rec.sets,
                            reps_min=self._parse_reps_min(exercise_rec.reps),
                            reps_max=self._parse_reps_max(exercise_rec.reps),
                            rest_seconds=self._parse_rest_seconds(exercise_rec.rest),
                            notes=f"추천 운동 - {exercise_rec.tips}" if exercise_rec.tips else None
                        )
                        
                        self.db.add(workout_exercise)
            
            self.db.commit()
            return workout_plan
            
        except Exception as e:
            self.db.rollback()
            print(f"운동 계획 저장 중 오류: {e}")
            return None


    def _parse_reps_min(self, reps_str: str) -> Optional[int]:
        """반복 횟수 문자열에서 최솟값 추출"""
        try:
            if '-' in reps_str:
                return int(reps_str.split('-')[0])
            elif reps_str.isdigit():
                return int(reps_str)
        except:
            pass
        return None


    def _parse_reps_max(self, reps_str: str) -> Optional[int]:
        """반복 횟수 문자열에서 최댓값 추출"""
        try:
            if '-' in reps_str:
                return int(reps_str.split('-')[1])
            elif reps_str.isdigit():
                return int(reps_str)
        except:
            pass
        return None


    def _parse_rest_seconds(self, rest_str: str) -> int:
        """휴식 시간 문자열을 초로 변환"""
        try:
            if '분' in rest_str:
                minutes = int(rest_str.replace('분', '').split('-')[0])
                return minutes * 60
            elif '초' in rest_str:
                return int(rest_str.replace('초', ''))
        except:
            pass
        return 120  # 기본값 2분

