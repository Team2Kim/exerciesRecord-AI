"""
운동 일지 분석 서비스
사용자의 운동 패턴을 분석하고 맞춤형 인사이트를 제공합니다.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict

from models.database import DailyLog, LogExercise, Exercise
from models.schemas import (
    BodyPartAnalysis, WorkoutPatternAnalysis, 
    WorkoutInsight, ComprehensiveAnalysis
)


class WorkoutAnalysisService:
    """운동 분석 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def analyze_workout_pattern(
        self, 
        user_id: str, 
        days: int = 30
    ) -> WorkoutPatternAnalysis:
        """
        사용자의 운동 패턴을 분석합니다.
        
        Args:
            user_id: 사용자 ID
            days: 분석 기간 (일)
            
        Returns:
            WorkoutPatternAnalysis: 운동 패턴 분석 결과
        """
        # 분석 기간 설정
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 해당 기간의 일지 조회
        logs = self.db.query(DailyLog).filter(
            DailyLog.user_id == user_id,
            DailyLog.date >= start_date.strftime("%Y-%m-%d"),
            DailyLog.date <= end_date.strftime("%Y-%m-%d")
        ).all()
        
        if not logs:
            # 데이터가 없으면 빈 분석 결과 반환
            return WorkoutPatternAnalysis(
                period_days=days,
                total_workouts=0,
                total_exercises=0,
                total_time=0,
                avg_workout_time=0.0,
                body_part_distribution=[],
                most_frequent_exercises=[],
                intensity_distribution={"상": 0, "중": 0, "하": 0}
            )
        
        # 통계 수집
        total_workouts = len(logs)
        all_log_exercises = []
        for log in logs:
            all_log_exercises.extend(log.log_exercises)
        
        total_exercises = len(all_log_exercises)
        total_time = sum(le.exercise_time for le in all_log_exercises)
        avg_workout_time = total_time / total_workouts if total_workouts > 0 else 0
        
        # 신체 부위별 분석
        body_part_stats = defaultdict(lambda: {
            'count': 0,
            'time': 0,
            'exercises': []
        })
        
        exercise_counter = Counter()
        intensity_counter = Counter()
        
        for log_exercise in all_log_exercises:
            exercise = log_exercise.exercise
            body_part = exercise.body_part
            
            # 신체 부위별 집계
            body_part_stats[body_part]['count'] += 1
            body_part_stats[body_part]['time'] += log_exercise.exercise_time
            if exercise.name not in body_part_stats[body_part]['exercises']:
                body_part_stats[body_part]['exercises'].append(exercise.name)
            
            # 운동 빈도 집계
            exercise_counter[(exercise.name, body_part)] += 1
            
            # 강도 집계
            intensity_counter[log_exercise.intensity] += 1
        
        # 신체 부위별 분석 결과 생성
        body_part_distribution = []
        for body_part, stats in body_part_stats.items():
            percentage = (stats['count'] / total_exercises * 100) if total_exercises > 0 else 0
            body_part_distribution.append(BodyPartAnalysis(
                body_part=body_part,
                exercise_count=stats['count'],
                total_time=stats['time'],
                percentage=round(percentage, 1),
                exercises=stats['exercises'][:5]  # 상위 5개만
            ))
        
        # 비율 높은 순으로 정렬
        body_part_distribution.sort(key=lambda x: x.percentage, reverse=True)
        
        # 가장 많이 한 운동 (상위 10개)
        most_frequent = [
            {
                'name': name,
                'body_part': body_part,
                'count': count
            }
            for (name, body_part), count in exercise_counter.most_common(10)
        ]
        
        # 강도 분포
        intensity_dist = {
            '상': intensity_counter.get('상', 0),
            '중': intensity_counter.get('중', 0),
            '하': intensity_counter.get('하', 0)
        }
        
        return WorkoutPatternAnalysis(
            period_days=days,
            total_workouts=total_workouts,
            total_exercises=total_exercises,
            total_time=total_time,
            avg_workout_time=round(avg_workout_time, 1),
            body_part_distribution=body_part_distribution,
            most_frequent_exercises=most_frequent,
            intensity_distribution=intensity_dist
        )
    
    def generate_insights(
        self,
        user_id: str,
        days: int = 30
    ) -> WorkoutInsight:
        """
        운동 패턴을 기반으로 인사이트를 생성합니다.
        
        Args:
            user_id: 사용자 ID
            days: 분석 기간 (일)
            
        Returns:
            WorkoutInsight: 인사이트 및 추천
        """
        pattern = self.analyze_workout_pattern(user_id, days)
        
        if pattern.total_exercises == 0:
            return WorkoutInsight(
                overworked_parts=[],
                underworked_parts=[],
                balance_score=0,
                recommendations=["운동 일지를 작성하면 맞춤 분석을 받을 수 있습니다."],
                warnings=[]
            )
        
        # 주요 신체 부위 정의
        major_body_parts = ["가슴", "등", "하체", "어깨", "팔", "코어"]
        
        # 신체 부위별 비율 계산
        body_part_ratios = {
            bp.body_part: bp.percentage 
            for bp in pattern.body_part_distribution
        }
        
        # 과사용 부위 (30% 이상)
        overworked = [
            bp for bp, ratio in body_part_ratios.items()
            if ratio >= 30
        ]
        
        # 부족한 부위 (10% 미만 또는 아예 안 함)
        underworked = [
            bp for bp in major_body_parts
            if body_part_ratios.get(bp, 0) < 10
        ]
        
        # 균형 점수 계산 (표준편차 기반)
        if len(body_part_ratios) >= 2:
            ratios = list(body_part_ratios.values())
            avg_ratio = sum(ratios) / len(ratios)
            variance = sum((r - avg_ratio) ** 2 for r in ratios) / len(ratios)
            std_dev = variance ** 0.5
            
            # 표준편차가 낮을수록 균형이 좋음
            # 0 std_dev = 100점, 30 이상 std_dev = 0점
            balance_score = max(0, 100 - (std_dev * 3.33))
        else:
            balance_score = 50  # 데이터 부족
        
        # 추천 사항 생성
        recommendations = []
        warnings = []
        
        if underworked:
            recommendations.append(
                f"부족한 부위: {', '.join(underworked)}에 집중하세요."
            )
        
        if overworked:
            warnings.append(
                f"과사용 부위: {', '.join(overworked)}는 휴식이 필요할 수 있습니다."
            )
        
        # 강도 분석
        intensity_dist = pattern.intensity_distribution
        total_intensity = sum(intensity_dist.values())
        if total_intensity > 0:
            high_ratio = intensity_dist['상'] / total_intensity * 100
            low_ratio = intensity_dist['하'] / total_intensity * 100
            
            if high_ratio > 70:
                warnings.append("고강도 운동 비율이 높습니다. 회복 시간을 충분히 가지세요.")
            elif low_ratio > 70:
                recommendations.append("운동 강도를 점진적으로 높여보세요.")
        
        # 균형 점수에 따른 추천
        if balance_score >= 80:
            recommendations.append("🎉 훌륭한 균형을 유지하고 있습니다!")
        elif balance_score >= 60:
            recommendations.append("✅ 양호한 운동 루틴입니다. 조금만 더 균형을 맞춰보세요.")
        else:
            recommendations.append("⚠️ 신체 부위 간 균형을 개선하는 것이 좋습니다.")
        
        # 운동 빈도 분석
        if pattern.total_workouts < (days / 7 * 2):  # 주 2회 미만
            recommendations.append("운동 빈도를 늘려보세요. 주 3-4회가 이상적입니다.")
        
        return WorkoutInsight(
            overworked_parts=overworked,
            underworked_parts=underworked,
            balance_score=round(balance_score, 1),
            recommendations=recommendations,
            warnings=warnings
        )
    
    def get_comprehensive_analysis(
        self,
        user_id: str,
        days: int = 30
    ) -> ComprehensiveAnalysis:
        """
        종합 운동 분석 결과를 반환합니다.
        
        Args:
            user_id: 사용자 ID
            days: 분석 기간 (일)
            
        Returns:
            ComprehensiveAnalysis: 종합 분석 결과
        """
        pattern = self.analyze_workout_pattern(user_id, days)
        insights = self.generate_insights(user_id, days)
        
        return ComprehensiveAnalysis(
            user_id=user_id,
            analysis_period=f"최근 {days}일",
            pattern=pattern,
            insights=insights
        )

