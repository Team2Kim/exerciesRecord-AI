// 운동 영상 관련 이벤트 핸들러들

// 영상 검색 폼 제출 처리
async function handleVideoSearch(event) {
    event.preventDefault();
    
    const options = {
        keyword: document.getElementById('videoKeyword').value.trim(),
        targetGroup: document.getElementById('videoTargetGroup').value,
        fitnessFactorName: document.getElementById('videoFitnessFactor').value,
        exerciseTool: document.getElementById('videoExerciseTool').value,
        page: 0,
        size: 12
    };
    
    const result = await searchExerciseVideos(options);
    
    if (result && result.success && result.data.content) {
        displayVideoResults(result.data.content, 'videoSearchResults');
        showToast(`${result.data.content.length}개의 영상을 찾았습니다.`, 'success');
    } else {
        displayVideoResults([], 'videoSearchResults');
        showToast('검색 결과가 없습니다.', 'info');
    }
}

// 근육별 검색 폼 제출 처리
async function handleMuscleSearch(event) {
    event.preventDefault();
    
    const muscleNames = document.getElementById('muscleNames').value
        .split(',')
        .map(name => name.trim())
        .filter(name => name.length > 0);
    
    if (muscleNames.length === 0) {
        showToast('근육 이름을 입력해주세요.', 'warning');
        return;
    }
    
    const result = await searchVideosByMuscle(muscleNames, 0, 12);
    
    if (result && result.success && result.data.content) {
        displayVideoResults(result.data.content, 'muscleSearchResults');
        showToast(`${result.data.content.length}개의 영상을 찾았습니다.`, 'success');
    } else {
        displayVideoResults([], 'muscleSearchResults');
        showToast('검색 결과가 없습니다.', 'info');
    }
}

// 인기 영상 로드
async function loadPopularVideos() {
    const targetGroup = document.getElementById('popularTargetGroup').value;
    
    const result = await getPopularVideos(targetGroup, 12);
    
    if (result && result.success && result.videos) {
        displayVideoResults(result.videos, 'popularVideos');
        showToast(`${result.videos.length}개의 인기 영상을 불러왔습니다.`, 'success');
    } else {
        displayVideoResults([], 'popularVideos');
        showToast('인기 영상을 불러올 수 없습니다.', 'error');
    }
}

// 외부 API 기반 추천 핸들러 (메인 기능)
async function handleExternalAPIRecommend(event) {
    const submitBtn = event.target || event.currentTarget;
    const originalText = submitBtn.innerHTML;
    
    try {
        // 로딩 상태 설정
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 영상 검색 중...';
        submitBtn.disabled = true;
        
        // 폼 데이터 수집
        const formData = {
            user_id: document.getElementById('userId').value,
            weekly_frequency: parseInt(document.getElementById('weeklyFrequency').value),
            split_type: document.getElementById('splitType').value,
            primary_goal: document.getElementById('primaryGoal').value,
            experience_level: document.getElementById('experienceLevel').value,
            available_time: parseInt(document.getElementById('availableTime').value),
            preferred_equipment: document.getElementById('preferredEquipment').value || null
        };
        
        // 외부 API 기반 추천 호출
        const recommendation = await getExternalAPIRecommendation(formData);
        
        if (recommendation && recommendation.success) {
            // 외부 API 기반 추천 결과 표시
            displayExternalRecommendation(recommendation);
            
            showToast('🎬 영상 기반 운동 추천이 완성되었습니다!', 'success');
            
            // 결과 섹션으로 스크롤
            setTimeout(() => {
                document.getElementById('recommendationResult').scrollIntoView({
                    behavior: 'smooth'
                });
            }, 100);
        } else {
            showToast('영상 기반 추천 생성에 실패했습니다.', 'error');
        }
        
    } catch (error) {
        console.error('외부 API 추천 오류:', error);
        showToast('영상 기반 추천 중 오류가 발생했습니다.', 'error');
    } finally {
        // 로딩 상태 해제
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// 외부 API 기반 추천 결과 표시
function displayExternalRecommendation(recommendation) {
    const resultContainer = document.getElementById('recommendationResult');
    const contentContainer = document.getElementById('recommendationContent');
    
    if (!recommendation.success) {
        contentContainer.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i> ${recommendation.message}
            </div>
        `;
        resultContainer.style.display = 'block';
        return;
    }
    
    let html = `
        <!-- 외부 API 기반 추천 헤더 -->
        <div class="alert alert-info mb-4">
            <i class="fas fa-video"></i> <strong>영상 기반 AI 추천</strong> - 실제 운동 영상 데이터를 활용한 맞춤형 추천입니다.
        </div>
        
        <!-- 요약 정보 -->
        <div class="row mb-4">
            <div class="col-md-3 text-center">
                <div class="stats-card">
                    <div class="icon text-primary">
                        <i class="fas fa-calendar-week"></i>
                    </div>
                    <h4>${recommendation.summary.total_days}일</h4>
                    <p class="text-muted">주간 운동</p>
                </div>
            </div>
            <div class="col-md-3 text-center">
                <div class="stats-card">
                    <div class="icon text-success">
                        <i class="fas fa-clock"></i>
                    </div>
                    <h4>${recommendation.total_weekly_duration}분</h4>
                    <p class="text-muted">총 시간</p>
                </div>
            </div>
            <div class="col-md-3 text-center">
                <div class="stats-card">
                    <div class="icon text-info">
                        <i class="fas fa-video"></i>
                    </div>
                    <h4>${recommendation.summary.total_exercises}개</h4>
                    <p class="text-muted">영상 운동</p>
                </div>
            </div>
            <div class="col-md-3 text-center">
                <div class="stats-card">
                    <div class="icon text-warning">
                        <i class="fas fa-star"></i>
                    </div>
                    <h4>${recommendation.difficulty_score}/5</h4>
                    <p class="text-muted">난이도</p>
                </div>
            </div>
        </div>
        
        <!-- 일별 운동 계획 -->
        <div class="row">
    `;
    
    Object.entries(recommendation.recommendation).forEach(([dayKey, dayData]) => {
        html += `
            <div class="col-lg-6 mb-4">
                <div class="card">
                    <div class="card-header bg-success text-white">
                        <h5 class="mb-0">
                            <i class="fas fa-play-circle"></i> ${dayKey} - ${dayData.day_name}
                        </h5>
                        <small class="text-light">
                            예상 시간: ${dayData.estimated_duration}분 | 
                            대상 부위: ${dayData.target_body_parts.join(', ')}
                        </small>
                    </div>
                    <div class="card-body">
        `;
        
        dayData.exercises.forEach((exercise, index) => {
            const hasVideo = exercise.video_url;
            const videoLength = exercise.video_length ? Math.floor(exercise.video_length / 60) : 0;
            
            html += `
                <div class="exercise-item p-3 mb-3 ${hasVideo ? 'border-success' : ''}">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="mb-0">${index + 1}. ${exercise.name}</h6>
                        <div>
                            <span class="badge bg-${exercise.difficulty === '초급' ? 'success' : exercise.difficulty === '중급' ? 'warning' : 'danger'} me-1">${exercise.difficulty}</span>
                            ${hasVideo ? `<span class="badge bg-info"><i class="fas fa-video"></i> ${videoLength}분</span>` : ''}
                        </div>
                    </div>
                    
                    <div class="row mb-2">
                        <div class="col-4">
                            <strong>세트:</strong> ${exercise.sets}
                        </div>
                        <div class="col-4">
                            <strong>횟수:</strong> ${exercise.reps}
                        </div>
                        <div class="col-4">
                            <strong>휴식:</strong> ${exercise.rest}
                        </div>
                    </div>
                    
                    ${exercise.weight ? `
                        <div class="mb-2">
                            <small class="text-muted"><strong>무게 가이드:</strong> ${exercise.weight}</small>
                        </div>
                    ` : ''}
                    
                    ${hasVideo ? `
                        <div class="text-center mb-2">
                            <button class="btn btn-success btn-sm" onclick="playVideo('${exercise.video_url}')">
                                <i class="fas fa-play"></i> 운동 영상 보기
                            </button>
                            ${exercise.image_url ? `
                                <img src="${exercise.image_url}" class="img-fluid rounded mt-2" alt="${exercise.name}" style="max-height: 80px;">
                            ` : ''}
                        </div>
                    ` : ''}
                    
                    <div class="exercise-details">
                        <small class="text-muted">
                            <i class="fas fa-bullseye"></i> ${exercise.body_part}
                        </small>
                        ${exercise.equipment ? `
                            <small class="text-muted ms-3">
                                <i class="fas fa-tools"></i> ${exercise.equipment}
                            </small>
                        ` : ''}
                        ${exercise.target_group ? `
                            <small class="text-muted ms-3">
                                <i class="fas fa-users"></i> ${exercise.target_group}
                            </small>
                        ` : ''}
                    </div>
                    
                    ${exercise.tips ? `
                        <div class="mt-2">
                            <small class="text-info">
                                <i class="fas fa-lightbulb"></i> ${exercise.tips}
                            </small>
                        </div>
                    ` : ''}
                </div>
            `;
        });
        
        html += `
                    </div>
                </div>
            </div>
        `;
    });
    
    html += `</div>`;
    
    // 팁 표시
    if (recommendation.tips && recommendation.tips.length > 0) {
        html += `
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card border-info">
                        <div class="card-header bg-info text-white">
                            <h5 class="mb-0">
                                <i class="fas fa-video"></i> 영상 운동 가이드
                            </h5>
                        </div>
                        <div class="card-body">
                            <ul class="list-unstyled mb-0">
        `;
        
        recommendation.tips.forEach(tip => {
            html += `<li class="mb-2"><i class="fas fa-play-circle text-info me-2"></i>${tip}</li>`;
        });
        
        html += `
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    contentContainer.innerHTML = html;
    resultContainer.style.display = 'block';
}

// 페이지 로드 시 인기 영상 자동 로드
document.addEventListener('DOMContentLoaded', function() {
    // 인기 영상 탭이 활성화될 때 자동 로드
    const popularTab = document.getElementById('popular-tab');
    if (popularTab) {
        popularTab.addEventListener('shown.bs.tab', function() {
            loadPopularVideos();
        });
    }
});
