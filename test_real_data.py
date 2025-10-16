"""
실제 운동 일지 데이터로 분석 테스트
"""

import json

# 제공받은 실제 데이터
real_data = {
    "success": True,
    "data": {
        "logId": 5,
        "date": "2025-10-16",
        "memo": "하체를 조졋슴당",
        "exercises": [
            {
                "logExerciseId": 15,
                "exercise": {
                    "exerciseId": 147,
                    "title": "바벨 앉았다 일어서기",
                    "videoUrl": "http://openapi.kspo.or.kr/web/video/0AUDLJ08S_00493.mp4",
                    "description": "근력 운동 중, 바벨 앉았다 일어서기운동을 설명한 운동처방 가이드 동영상",
                    "trainingName": "바벨 앉았다 일어서기",
                    "targetGroup": "공통",
                    "fitnessFactorName": "근력",
                    "fitnessLevelName": "4~5",
                    "bodyPart": None,
                    "exerciseTool": "바벨",
                    "videoLengthSeconds": 64,
                    "resolution": "1280*720",
                    "fpsCount": 29.96,
                    "imageFileName": "0AUDLJ08S_00493_SC_00005.jpeg",
                    "imageUrl": "http://openapi.kspo.or.kr/web/image/0AUDLJ08S_00493/",
                    "fileSize": 10711481,
                    "trainingAimName": None,
                    "trainingPlaceName": "헬스장",
                    "trainingSectionName": None,
                    "trainingStepName": None,
                    "trainingSequenceName": None,
                    "trainingWeekName": None,
                    "repetitionCountName": "",
                    "setCountName": "",
                    "operationName": None,
                    "jobYmd": "20220922",
                    "muscles": [],
                    "gookmin100": True
                },
                "intensity": "상",
                "exerciseTime": 30
            },
            {
                "logExerciseId": 16,
                "exercise": {
                    "exerciseId": 128,
                    "title": "앉아서 다리 밀기",
                    "videoUrl": "http://openapi.kspo.or.kr/web/video/0AUDLJ08S_00474.mp4",
                    "description": "근력 운동 중, 앉아서 다리 밀기운동을 설명한 운동처방 가이드 동영상",
                    "trainingName": "앉아서 다리 밀기",
                    "targetGroup": "공통",
                    "fitnessFactorName": "근력",
                    "fitnessLevelName": "3~5",
                    "bodyPart": None,
                    "exerciseTool": "헬스기구",
                    "videoLengthSeconds": 65,
                    "resolution": "1280*720",
                    "fpsCount": 29.96,
                    "imageFileName": "0AUDLJ08S_00474_SC_00005.jpeg",
                    "imageUrl": "http://openapi.kspo.or.kr/web/image/0AUDLJ08S_00474/",
                    "fileSize": 10425448,
                    "trainingAimName": None,
                    "trainingPlaceName": "헬스장",
                    "trainingStepName": None,
                    "trainingSequenceName": None,
                    "trainingWeekName": None,
                    "repetitionCountName": "",
                    "setCountName": "",
                    "operationName": None,
                    "jobYmd": "20220930",
                    "muscles": ["넙다리네갈래근"],
                    "gookmin100": True
                },
                "intensity": "중",
                "exerciseTime": 15
            },
            {
                "logExerciseId": 17,
                "exercise": {
                    "exerciseId": 129,
                    "title": "앉아서 다리 펴기",
                    "videoUrl": "http://openapi.kspo.or.kr/web/video/0AUDLJ08S_00475.mp4",
                    "description": "근력 운동 중, 앉아서 앉아서 다리 펴기운동을 설명한 운동처방 가이드 동영상",
                    "trainingName": "앉아서 다리 펴기",
                    "targetGroup": "공통",
                    "fitnessFactorName": "근력",
                    "fitnessLevelName": "3~5",
                    "bodyPart": None,
                    "exerciseTool": "헬스기구",
                    "videoLengthSeconds": 51,
                    "resolution": "1280*720",
                    "fpsCount": 29.96,
                    "imageFileName": "0AUDLJ08S_00475_SC_00022.jpeg",
                    "imageUrl": "http://openapi.kspo.or.kr/web/image/0AUDLJ08S_00475/",
                    "fileSize": 7946936,
                    "trainingAimName": None,
                    "trainingPlaceName": "헬스장",
                    "trainingStepName": None,
                    "trainingSequenceName": None,
                    "trainingWeekName": None,
                    "repetitionCountName": "",
                    "setCountName": "",
                    "operationName": None,
                    "jobYmd": "20221001",
                    "muscles": ["넙다리네갈래근"],
                    "gookmin100": True
                },
                "intensity": "중",
                "exerciseTime": 15
            }
        ]
    },
    "date": "2025-10-16"
}

def analyze_daily_workout(workout_data):
    """운동 일지 데이터 분석 함수 (main.py와 동일)"""
    try:
        exercises = workout_data.get("exercises", [])
        
        if not exercises:
            return {
                "summary": "운동 기록이 없습니다.",
                "total_exercises": 0,
                "total_time": 0,
                "recommendations": ["운동을 시작해보세요!"]
            }
        
        # 기본 통계 계산
        total_exercises = len(exercises)
        total_time = sum(ex.get("exerciseTime", 0) for ex in exercises)
        avg_time_per_exercise = total_time / total_exercises if total_exercises > 0 else 0
        
        # 강도 분석
        intensity_dist = {"상": 0, "중": 0, "하": 0}
        for ex in exercises:
            intensity = ex.get("intensity", "중")
            if intensity in intensity_dist:
                intensity_dist[intensity] += 1
        
        # 운동 부위 분석 (bodyPart이 null인 경우 exerciseTool로 대체)
        body_parts = {}
        exercise_tools = {}
        muscles = set()
        
        for ex in exercises:
            exercise_info = ex.get("exercise", {})
            
            # 운동 부위 (bodyPart이 null이면 exerciseTool 사용)
            body_part = exercise_info.get("bodyPart")
            if not body_part:
                body_part = exercise_info.get("exerciseTool", "기타")
            body_parts[body_part] = body_parts.get(body_part, 0) + 1
            
            # 운동 도구
            tool = exercise_info.get("exerciseTool", "기타")
            exercise_tools[tool] = exercise_tools.get(tool, 0) + 1
            
            # 근육 부위
            ex_muscles = exercise_info.get("muscles", [])
            for muscle in ex_muscles:
                muscles.add(muscle)
        
        # 가장 많이 한 운동
        most_frequent_body_part = max(body_parts.items(), key=lambda x: x[1]) if body_parts else ("없음", 0)
        most_used_tool = max(exercise_tools.items(), key=lambda x: x[1]) if exercise_tools else ("없음", 0)
        
        # 강도별 비율 계산
        total_intensity = sum(intensity_dist.values())
        intensity_percentage = {}
        for intensity, count in intensity_dist.items():
            intensity_percentage[intensity] = round((count / total_intensity * 100), 1) if total_intensity > 0 else 0
        
        # AI 분석 및 추천사항 생성
        recommendations = []
        warnings = []
        insights = []
        
        # 강도 분석
        if intensity_percentage.get("상", 0) > 60:
            warnings.append("고강도 운동 비율이 높습니다. 충분한 휴식을 취하세요.")
        elif intensity_percentage.get("하", 0) > 60:
            recommendations.append("운동 강도를 점진적으로 높여보세요.")
        
        # 운동 시간 분석
        if avg_time_per_exercise > 30:
            insights.append(f"운동당 평균 {avg_time_per_exercise:.1f}분으로 충분한 시간을 투자하고 있습니다.")
        elif avg_time_per_exercise < 10:
            recommendations.append("운동 시간을 조금 더 늘려보세요.")
        
        # 운동 다양성 분석
        if len(body_parts) == 1:
            recommendations.append("다양한 신체 부위를 운동해보세요.")
        else:
            insights.append(f"{len(body_parts)}개 부위를 골고루 운동했습니다.")
        
        # 특정 운동에 대한 분석
        for ex in exercises:
            exercise_info = ex.get("exercise", {})
            exercise_name = exercise_info.get("title", "")
            exercise_time = ex.get("exerciseTime", 0)
            intensity = ex.get("intensity", "")
            
            if "하체" in exercise_name or "다리" in exercise_name or "스쿼트" in exercise_name:
                insights.append(f"하체 운동 '{exercise_name}'을 {exercise_time}분간 {intensity}강도로 수행했습니다.")
        
        # 메모 분석
        memo = workout_data.get("memo", "")
        if memo:
            insights.append(f"메모: {memo}")
        
        # 결과 구성
        workout_date = workout_data.get("date", "해당 날짜")
        analysis_result = {
            "summary": f"{workout_date}에 {total_exercises}개 운동을 총 {total_time}분간 수행했습니다.",
            "statistics": {
                "total_exercises": total_exercises,
                "total_time": total_time,
                "avg_time_per_exercise": round(avg_time_per_exercise, 1),
                "intensity_distribution": intensity_dist,
                "intensity_percentage": intensity_percentage,
                "body_parts_trained": body_parts,
                "exercise_tools_used": exercise_tools,
                "muscles_targeted": list(muscles)
            },
            "insights": insights,
            "recommendations": recommendations,
            "warnings": warnings,
            "highlights": {
                "most_frequent_body_part": most_frequent_body_part,
                "most_used_tool": most_used_tool,
                "dominant_intensity": max(intensity_dist.items(), key=lambda x: x[1]) if total_intensity > 0 else ("없음", 0)
            }
        }
        
        return analysis_result
        
    except Exception as e:
        return {
            "error": f"분석 중 오류 발생: {str(e)}",
            "summary": "운동 데이터 분석에 실패했습니다."
        }

def main():
    """실제 데이터로 분석 테스트"""
    print("=" * 60)
    print("🧪 실제 운동 일지 데이터 분석 테스트")
    print("=" * 60)
    
    workout_data = real_data["data"]
    
    print(f"📅 날짜: {workout_data['date']}")
    print(f"📝 메모: {workout_data['memo']}")
    print(f"💪 운동 개수: {len(workout_data['exercises'])}")
    print()
    
    # 분석 실행
    analysis = analyze_daily_workout(workout_data)
    
    print("🤖 AI 분석 결과:")
    print(f"📋 요약: {analysis['summary']}")
    print()
    
    # 통계 정보
    stats = analysis['statistics']
    print("📊 통계:")
    print(f"   - 총 운동 시간: {stats['total_time']}분")
    print(f"   - 운동당 평균 시간: {stats['avg_time_per_exercise']}분")
    print(f"   - 강도 분포: 상({stats['intensity_distribution']['상']}) 중({stats['intensity_distribution']['중']}) 하({stats['intensity_distribution']['하']})")
    print(f"   - 운동 도구: {', '.join([f'{tool}({count})' for tool, count in stats['exercise_tools_used'].items()])}")
    print(f"   - 타겟 근육: {', '.join(stats['muscles_targeted']) if stats['muscles_targeted'] else '없음'}")
    print()
    
    # 하이라이트
    highlights = analysis['highlights']
    print("⭐ 하이라이트:")
    print(f"   - 주 운동 도구: {highlights['most_used_tool'][0]} ({highlights['most_used_tool'][1]}회)")
    print(f"   - 주 강도: {highlights['dominant_intensity'][0]} ({highlights['dominant_intensity'][1]}회)")
    print()
    
    # 인사이트
    if analysis['insights']:
        print("💡 인사이트:")
        for insight in analysis['insights']:
            print(f"   - {insight}")
        print()
    
    # 추천사항
    if analysis['recommendations']:
        print("💪 추천사항:")
        for rec in analysis['recommendations']:
            print(f"   - {rec}")
        print()
    
    # 주의사항
    if analysis['warnings']:
        print("⚠️ 주의사항:")
        for warning in analysis['warnings']:
            print(f"   - {warning}")
        print()
    
    print("=" * 60)
    print("✅ 분석 완료!")
    print()
    print("💡 이제 API에서 이런 분석 결과를 받을 수 있습니다!")

if __name__ == "__main__":
    main()
