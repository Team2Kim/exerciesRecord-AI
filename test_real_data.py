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
        
        # 운동 부위 분석 (운동 이름과 설명을 기반으로 부위 추출)
        body_parts = {}
        exercise_tools = {}
        muscles = set()
        
        def extract_body_part_from_exercise(exercise_info):
            """운동 이름과 설명에서 신체 부위를 추출"""
            title = exercise_info.get("title", "").lower()
            description = exercise_info.get("description", "").lower()
            training_name = exercise_info.get("trainingName", "").lower()
            
            # 하체 관련 키워드
            lower_body_keywords = ["다리", "하체", "스쿼트", "앉아서", "일어서기", "밀기", "펴기", "넙다리", "대퇴", "허벅지", "종아리", "발목"]
            # 상체 관련 키워드
            upper_body_keywords = ["가슴", "어깨", "팔", "등", "코어", "복부", "벤치", "프레스", "풀업", "덤벨", "로우"]
            
            # 하체 확인
            for keyword in lower_body_keywords:
                if keyword in title or keyword in description or keyword in training_name:
                    return "하체"
            
            # 상체 확인
            for keyword in upper_body_keywords:
                if keyword in title or keyword in description or keyword in training_name:
                    return "상체"
            
            # 기본값
            return "전신"
        
        for ex in exercises:
            exercise_info = ex.get("exercise", {})
            
            # 운동 부위 추출 (운동 이름 기반)
            body_part = exercise_info.get("bodyPart")
            if not body_part:
                body_part = extract_body_part_from_exercise(exercise_info)
            body_parts[body_part] = body_parts.get(body_part, 0) + 1
            
            # 운동 도구 (원본 그대로)
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
        
        # 상세 AI 분석 및 추천사항 생성
        recommendations = []
        warnings = []
        insights = []
        
        # 1. 강도 분석 (더 세분화)
        high_intensity_ratio = intensity_percentage.get("상", 0)
        medium_intensity_ratio = intensity_percentage.get("중", 0)
        low_intensity_ratio = intensity_percentage.get("하", 0)
        
        if high_intensity_ratio > 70:
            warnings.append(f"고강도 운동이 {high_intensity_ratio}%로 매우 높습니다. 근육 회복을 위해 충분한 휴식을 취하고 단백질 섭취를 늘리세요.")
            recommendations.append("다음 운동은 중강도로 조절하여 과부하를 방지하세요.")
        elif high_intensity_ratio > 50:
            warnings.append(f"고강도 운동이 {high_intensity_ratio}%로 높습니다. 운동 후 스트레칭과 충분한 수면을 취하세요.")
        elif low_intensity_ratio > 70:
            recommendations.append(f"저강도 운동이 {low_intensity_ratio}%로 높습니다. 점진적으로 운동 강도를 높여 체력 향상을 도모하세요.")
        elif medium_intensity_ratio > 60:
            insights.append(f"중강도 운동 비율이 {medium_intensity_ratio}%로 적절한 강도 조절을 하고 있습니다.")
        
        # 2. 운동 시간 분석 (더 구체적)
        if avg_time_per_exercise > 45:
            insights.append(f"운동당 평균 {avg_time_per_exercise:.1f}분으로 매우 충분한 시간을 투자하고 있습니다. 집중력과 자세 유지가 우수합니다.")
        elif avg_time_per_exercise > 30:
            insights.append(f"운동당 평균 {avg_time_per_exercise:.1f}분으로 적절한 운동 시간입니다.")
        elif avg_time_per_exercise > 15:
            recommendations.append(f"운동당 평균 {avg_time_per_exercise:.1f}분으로 조금 짧습니다. 각 세트 간 휴식을 줄이고 운동 시간을 20-30분으로 늘려보세요.")
        else:
            warnings.append(f"운동당 평균 {avg_time_per_exercise:.1f}분으로 너무 짧습니다. 운동 효과를 높이기 위해 시간을 늘리는 것을 권장합니다.")
        
        # 3. 운동 다양성 및 균형 분석
        body_part_count = len(body_parts)
        if body_part_count == 1:
            main_part = list(body_parts.keys())[0]
            warnings.append(f"오늘은 {main_part}만 집중적으로 운동했습니다. 근육 불균형을 방지하기 위해 다음 운동에서는 다른 부위도 포함하세요.")
            recommendations.append(f"상체 운동을 추가하여 전신 균형을 맞춰보세요.")
        elif body_part_count == 2:
            parts = list(body_parts.keys())
            insights.append(f"{parts[0]}와 {parts[1]} 부위를 균형있게 운동했습니다.")
        elif body_part_count >= 3:
            insights.append(f"{body_part_count}개 부위를 종합적으로 운동하여 전신 균형이 우수합니다.")
        
        # 4. 운동 도구 다양성 분석
        tool_count = len(exercise_tools)
        if tool_count == 1:
            tool = list(exercise_tools.keys())[0]
            recommendations.append(f"오늘은 {tool}만 사용했습니다. 다양한 도구를 활용하여 운동의 다양성을 높여보세요.")
        elif tool_count >= 2:
            insights.append(f"{tool_count}가지 운동 도구를 활용하여 다양한 자극을 주었습니다.")
        
        # 5. 근육 타겟 분석
        muscle_count = len(muscles)
        if muscle_count > 0:
            insights.append(f"주요 타겟 근육: {', '.join(muscles)}")
            if "넙다리네갈래근" in muscles:
                recommendations.append("넙다리네갈래근을 집중적으로 운동했습니다. 운동 후 스트레칭으로 유연성을 유지하세요.")
        
        # 6. 개별 운동 상세 분석
        exercise_details = []
        for ex in exercises:
            exercise_info = ex.get("exercise", {})
            exercise_name = exercise_info.get("title", "")
            exercise_time = ex.get("exerciseTime", 0)
            intensity = ex.get("intensity", "")
            tool = exercise_info.get("exerciseTool", "")
            
            # 운동별 맞춤 분석
            if "스쿼트" in exercise_name or "앉았다" in exercise_name:
                if intensity == "상" and exercise_time > 25:
                    exercise_details.append(f"'{exercise_name}': 고강도로 충분한 시간 운동했습니다. 대퇴사두근과 둔근 발달에 효과적입니다.")
                elif intensity == "중":
                    exercise_details.append(f"'{exercise_name}': 적절한 강도로 운동했습니다. 자세에 집중하여 안전하게 수행하세요.")
            
            elif "다리" in exercise_name and ("밀기" in exercise_name or "펴기" in exercise_name):
                if exercise_time < 15:
                    exercise_details.append(f"'{exercise_name}': {exercise_time}분은 조금 짧습니다. 15-20분으로 늘리면 더 효과적입니다.")
                else:
                    exercise_details.append(f"'{exercise_name}': {exercise_time}분간 {intensity}강도로 적절히 운동했습니다.")
        
        insights.extend(exercise_details)
        
        # 7. 운동 순서 및 조합 분석
        if len(exercises) >= 2:
            first_exercise = exercises[0]["exercise"]["title"]
            last_exercise = exercises[-1]["exercise"]["title"]
            insights.append(f"운동 순서: '{first_exercise}' → '{last_exercise}'로 구성되어 있습니다.")
            
            # 복합운동 vs 고립운동 분석
            compound_exercises = []
            isolation_exercises = []
            
            for ex in exercises:
                exercise_name = ex["exercise"]["title"]
                if any(keyword in exercise_name for keyword in ["스쿼트", "데드리프트", "벤치프레스", "풀업", "앉았다"]):
                    compound_exercises.append(exercise_name)
                else:
                    isolation_exercises.append(exercise_name)
            
            if compound_exercises and isolation_exercises:
                insights.append(f"복합운동({len(compound_exercises)}개)과 고립운동({len(isolation_exercises)}개)을 적절히 조합했습니다.")
            elif compound_exercises:
                insights.append(f"복합운동 위주로 구성되어 효율적인 운동입니다.")
        
        # 8. 메모 감정 분석
        memo = workout_data.get("memo", "")
        if memo:
            insights.append(f"운동 메모: '{memo}'")
            if any(word in memo for word in ["힘들", "어려", "고생", "조졋"]):
                insights.append("운동이 힘들었던 것 같습니다. 점진적으로 강도를 조절하여 지속 가능한 운동을 하세요.")
                recommendations.append("운동 전 충분한 워밍업과 운동 후 쿨다운을 실시하세요.")
            elif any(word in memo for word in ["좋", "만족", "성공", "완료"]):
                insights.append("운동에 만족하고 계시는군요! 꾸준한 운동으로 목표를 달성하세요.")
        
        # 9. 운동 강도별 상세 추천
        if high_intensity_ratio > 50:
            recommendations.append("고강도 운동 후에는 단백질 보충제나 BCAA 섭취를 고려하세요.")
        
        if total_time > 90:
            recommendations.append("장시간 운동 후에는 충분한 수분 섭취와 전해질 보충이 필요합니다.")
        
        # 10. 다음 운동 계획 제안
        if body_part_count == 1:
            main_part = list(body_parts.keys())[0]
            if main_part == "하체":
                recommendations.append("다음 운동에서는 상체(가슴, 등, 어깨) 운동을 추가하여 균형을 맞춰보세요.")
            elif main_part == "상체":
                recommendations.append("다음 운동에서는 하체(스쿼트, 런지 등) 운동을 추가하여 균형을 맞춰보세요.")
        
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
    print(f"   - 운동 부위: {', '.join([f'{part}({count})' for part, count in stats['body_parts_trained'].items()])}")
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
