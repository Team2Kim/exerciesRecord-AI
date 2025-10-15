// ExRecAI 웹 애플리케이션 JavaScript

// 전역 상수
const API_BASE_URL = '';  // 같은 도메인 사용
const TOAST_DURATION = 3000;

// 전역 변수
let exercises = [];
let filteredExercises = [];
let filterOptions = {
    bodyParts: [],
    categories: [],
    difficulties: [],
    targetGoals: []
};

// 페이지 로드시 초기화
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// 앱 초기화
async function initializeApp() {
    try {
        // 필터 옵션 로드
        await loadFilterOptions();
        
        // 운동 데이터 로드
        await loadExercises();
        
        // 통계 데이터 로드
        await loadStatistics();
        
        // 이벤트 리스너 설정
        setupEventListeners();
        
        showToast('앱이 성공적으로 로드되었습니다!', 'success');
    } catch (error) {
        console.error('앱 초기화 오류:', error);
        showToast('앱 로드 중 오류가 발생했습니다.', 'error');
    }
}

// 이벤트 리스너 설정
function setupEventListeners() {
    // 추천 폼 제출
    document.getElementById('recommendForm').addEventListener('submit', handleRecommendSubmit);
    
    // 운동 검색
    document.getElementById('exerciseSearch').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchExercises();
        }
    });
    
    // 스무스 스크롤 for 네비게이션
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
}

// API 호출 유틸리티
async function apiCall(endpoint, options = {}) {
    const config = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
        ...options
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API 호출 오류:', error);
        throw error;
    }
}

// 필터 옵션 로드
async function loadFilterOptions() {
    try {
        const data = await apiCall('/api/filters');
        filterOptions = data;
        
        // 필터 드롭다운 채우기
        populateFilterDropdowns();
    } catch (error) {
        console.error('필터 옵션 로드 오류:', error);
    }
}

// 필터 드롭다운 채우기
function populateFilterDropdowns() {
    // 운동 부위 필터
    const bodyPartSelect = document.getElementById('bodyPartFilter');
    filterOptions.body_parts.forEach(part => {
        const option = document.createElement('option');
        option.value = part;
        option.textContent = part;
        bodyPartSelect.appendChild(option);
    });
    
    // 카테고리 필터
    const categorySelect = document.getElementById('categoryFilter');
    filterOptions.categories.forEach(category => {
        const option = document.createElement('option');
        option.value = category;
        option.textContent = category;
        categorySelect.appendChild(option);
    });
    
    // 난이도 필터
    const difficultySelect = document.getElementById('difficultyFilter');
    filterOptions.difficulties.forEach(difficulty => {
        const option = document.createElement('option');
        option.value = difficulty;
        option.textContent = difficulty;
        difficultySelect.appendChild(option);
    });
}

// 운동 데이터 로드
async function loadExercises() {
    const loadingElement = document.getElementById('exerciseLoading');
    const listElement = document.getElementById('exerciseList');
    
    try {
        loadingElement.style.display = 'block';
        listElement.innerHTML = '';
        
        exercises = await apiCall('/api/exercises?limit=50');
        filteredExercises = [...exercises];
        
        displayExercises(filteredExercises);
    } catch (error) {
        console.error('운동 데이터 로드 오류:', error);
        showToast('운동 데이터를 불러올 수 없습니다.', 'error');
    } finally {
        loadingElement.style.display = 'none';
    }
}

// 운동 표시
function displayExercises(exerciseList) {
    const container = document.getElementById('exerciseList');
    container.innerHTML = '';
    
    if (exerciseList.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center py-5">
                <i class="fas fa-search fa-3x text-muted mb-3"></i>
                <h4 class="text-muted">검색 결과가 없습니다</h4>
                <p class="text-muted">다른 검색어나 필터를 시도해보세요.</p>
            </div>
        `;
        return;
    }
    
    exerciseList.forEach(exercise => {
        const card = createExerciseCard(exercise);
        container.appendChild(card);
    });
}

// 운동 카드 생성
function createExerciseCard(exercise) {
    const col = document.createElement('div');
    col.className = 'col-lg-4 col-md-6 mb-4';
    
    col.innerHTML = `
        <div class="card exercise-card h-100" onclick="showExerciseDetail(${exercise.id})">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h5 class="card-title mb-0">${exercise.name}</h5>
                    <span class="badge difficulty-${exercise.difficulty} ms-2">${exercise.difficulty}</span>
                </div>
                ${exercise.name_en ? `<p class="text-muted small mb-2">${exercise.name_en}</p>` : ''}
                
                <div class="mb-3">
                    <span class="badge category-${exercise.category} me-2">${exercise.category}</span>
                    <span class="badge bg-secondary">${exercise.body_part}</span>
                </div>
                
                <div class="exercise-details">
                    <div class="row text-center">
                        <div class="col-4">
                            <small class="text-muted">목표</small>
                            <div class="fw-bold">${exercise.target_goal}</div>
                        </div>
                        <div class="col-4">
                            <small class="text-muted">시간</small>
                            <div class="fw-bold">${exercise.duration}분</div>
                        </div>
                        <div class="col-4">
                            <small class="text-muted">칼로리</small>
                            <div class="fw-bold">${exercise.calories_per_minute ? Math.round(exercise.calories_per_minute * exercise.duration) : 'N/A'}</div>
                        </div>
                    </div>
                </div>
                
                ${exercise.equipment ? `
                    <div class="mt-2">
                        <small class="text-muted">필요 장비:</small>
                        <small>${exercise.equipment}</small>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
    
    return col;
}

// 운동 상세 정보 모달 표시
function showExerciseDetail(exerciseId) {
    const exercise = exercises.find(ex => ex.id === exerciseId);
    if (!exercise) return;
    
    // 모달 HTML 생성
    const modalHtml = `
        <div class="modal fade" id="exerciseDetailModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            ${exercise.name} ${exercise.name_en ? `(${exercise.name_en})` : ''}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>기본 정보</h6>
                                <ul class="list-unstyled">
                                    <li><strong>운동 부위:</strong> ${exercise.body_part}</li>
                                    <li><strong>카테고리:</strong> ${exercise.category}</li>
                                    <li><strong>난이도:</strong> ${exercise.difficulty}</li>
                                    <li><strong>목표:</strong> ${exercise.target_goal}</li>
                                    <li><strong>예상 시간:</strong> ${exercise.duration}분</li>
                                    ${exercise.equipment ? `<li><strong>필요 장비:</strong> ${exercise.equipment}</li>` : ''}
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <h6>세부 정보</h6>
                                <ul class="list-unstyled">
                                    ${exercise.muscle_group ? `<li><strong>근육군:</strong> ${exercise.muscle_group}</li>` : ''}
                                    ${exercise.calories_per_minute ? `<li><strong>분당 칼로리:</strong> ${exercise.calories_per_minute}kcal</li>` : ''}
                                    <li><strong>총 칼로리:</strong> ${exercise.calories_per_minute ? Math.round(exercise.calories_per_minute * exercise.duration) : 'N/A'}kcal</li>
                                </ul>
                            </div>
                        </div>
                        
                        ${exercise.instructions ? `
                            <div class="mt-4">
                                <h6>운동 방법</h6>
                                <p class="text-muted">${exercise.instructions}</p>
                            </div>
                        ` : ''}
                        
                        ${exercise.tips ? `
                            <div class="mt-3">
                                <h6>주의사항 및 팁</h6>
                                <p class="text-info">${exercise.tips}</p>
                            </div>
                        ` : ''}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">닫기</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 기존 모달 제거
    const existingModal = document.getElementById('exerciseDetailModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 새 모달 추가 및 표시
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('exerciseDetailModal'));
    modal.show();
}

// 운동 검색
async function searchExercises() {
    const searchTerm = document.getElementById('exerciseSearch').value.trim();
    
    if (!searchTerm) {
        filteredExercises = [...exercises];
        displayExercises(filteredExercises);
        return;
    }
    
    try {
        const data = await apiCall(`/api/exercises/search?q=${encodeURIComponent(searchTerm)}`);
        filteredExercises = data.results;
        displayExercises(filteredExercises);
        
        showToast(`${data.count}개의 운동을 찾았습니다.`, 'info');
    } catch (error) {
        console.error('검색 오류:', error);
        showToast('검색 중 오류가 발생했습니다.', 'error');
    }
}

// 운동 필터링
function filterExercises() {
    const bodyPart = document.getElementById('bodyPartFilter').value;
    const category = document.getElementById('categoryFilter').value;
    const difficulty = document.getElementById('difficultyFilter').value;
    
    filteredExercises = exercises.filter(exercise => {
        return (!bodyPart || exercise.body_part === bodyPart) &&
               (!category || exercise.category === category) &&
               (!difficulty || exercise.difficulty === difficulty);
    });
    
    displayExercises(filteredExercises);
}

// 추천 폼 제출 처리
async function handleRecommendSubmit(event) {
    event.preventDefault();
    
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    try {
        // 로딩 상태 설정
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 생성 중...';
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
        
        // API 호출
        const recommendation = await apiCall('/api/recommend', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        // 결과 표시
        displayRecommendation(recommendation);
        
        showToast('운동 추천이 성공적으로 생성되었습니다!', 'success');
        
        // 결과 섹션으로 스크롤
        setTimeout(() => {
            document.getElementById('recommendationResult').scrollIntoView({
                behavior: 'smooth'
            });
        }, 100);
        
    } catch (error) {
        console.error('추천 생성 오류:', error);
        showToast('추천 생성 중 오류가 발생했습니다.', 'error');
    } finally {
        // 로딩 상태 해제
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// 추천 결과 표시
function displayRecommendation(recommendation) {
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
                        <i class="fas fa-dumbbell"></i>
                    </div>
                    <h4>${recommendation.summary.total_exercises}개</h4>
                    <p class="text-muted">총 운동</p>
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
                    <div class="card-header">
                        <h5 class="mb-0">
                            <i class="fas fa-calendar-day"></i> ${dayKey} - ${dayData.day_name}
                        </h5>
                        <small class="text-muted">
                            예상 시간: ${dayData.estimated_duration}분 | 
                            대상 부위: ${dayData.target_body_parts.join(', ')}
                        </small>
                    </div>
                    <div class="card-body">
        `;
        
        dayData.exercises.forEach((exercise, index) => {
            html += `
                <div class="exercise-item p-3 mb-3">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="mb-0">${index + 1}. ${exercise.name}</h6>
                        <span class="badge difficulty-${exercise.difficulty}">${exercise.difficulty}</span>
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
                    
                    <div class="exercise-details">
                        <small class="text-muted">
                            <i class="fas fa-bullseye"></i> ${exercise.body_part}
                        </small>
                        ${exercise.equipment ? `
                            <small class="text-muted ms-3">
                                <i class="fas fa-tools"></i> ${exercise.equipment}
                            </small>
                        ` : ''}
                        ${exercise.weight ? `
                            <small class="text-muted ms-3">
                                <i class="fas fa-weight-hanging"></i> ${exercise.weight}
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
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">
                                <i class="fas fa-lightbulb"></i> 추천 팁
                            </h5>
                        </div>
                        <div class="card-body">
                            <ul class="list-unstyled mb-0">
        `;
        
        recommendation.tips.forEach(tip => {
            html += `<li class="mb-2"><i class="fas fa-check text-success me-2"></i>${tip}</li>`;
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

// 통계 데이터 로드
async function loadStatistics() {
    try {
        const stats = await apiCall('/api/stats');
        displayStatistics(stats);
    } catch (error) {
        console.error('통계 로드 오류:', error);
        document.getElementById('statisticsContent').innerHTML = `
            <div class="col-12 text-center">
                <p class="text-muted">통계를 불러올 수 없습니다.</p>
            </div>
        `;
    }
}

// 통계 표시
function displayStatistics(stats) {
    const container = document.getElementById('statisticsContent');
    
    const html = `
        <div class="col-lg-3 col-md-6 mb-4">
            <div class="card stats-card text-center">
                <div class="card-body">
                    <div class="icon text-primary mb-3">
                        <i class="fas fa-dumbbell fa-3x"></i>
                    </div>
                    <h3>${stats.total_exercises}</h3>
                    <p class="text-muted mb-0">총 운동 개수</p>
                </div>
            </div>
        </div>
        
        <div class="col-lg-3 col-md-6 mb-4">
            <div class="card stats-card text-center">
                <div class="card-body">
                    <div class="icon text-success mb-3">
                        <i class="fas fa-users fa-3x"></i>
                    </div>
                    <h3>${stats.total_users}</h3>
                    <p class="text-muted mb-0">사용자 수</p>
                </div>
            </div>
        </div>
        
        <div class="col-lg-3 col-md-6 mb-4">
            <div class="card stats-card text-center">
                <div class="card-body">
                    <div class="icon text-info mb-3">
                        <i class="fas fa-chart-line fa-3x"></i>
                    </div>
                    <h3>${stats.total_plans}</h3>
                    <p class="text-muted mb-0">생성된 계획</p>
                </div>
            </div>
        </div>
        
        <div class="col-lg-3 col-md-6 mb-4">
            <div class="card stats-card text-center">
                <div class="card-body">
                    <div class="icon text-warning mb-3">
                        <i class="fas fa-star fa-3x"></i>
                    </div>
                    <h3>${stats.total_feedback}</h3>
                    <p class="text-muted mb-0">피드백 수</p>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// 토스트 알림 표시
function showToast(message, type = 'info') {
    const toast = document.getElementById('alertToast');
    const toastBody = document.getElementById('toastMessage');
    
    // 타입별 스타일 적용
    toast.className = `toast toast-${type}`;
    
    // 아이콘 설정
    const icons = {
        success: 'fas fa-check-circle text-success',
        error: 'fas fa-exclamation-circle text-danger',
        info: 'fas fa-info-circle text-info',
        warning: 'fas fa-exclamation-triangle text-warning'
    };
    
    toastBody.innerHTML = `
        <i class="${icons[type] || icons.info}"></i> ${message}
    `;
    
    // 토스트 표시
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

// 유틸리티 함수들
function scrollToSection(sectionId) {
    const element = document.getElementById(sectionId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

// 숫자 포맷팅
function formatNumber(num) {
    return new Intl.NumberFormat('ko-KR').format(num);
}

// 날짜 포맷팅
function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('ko-KR');
}

// 로컬 스토리지 유틸리티
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
    } catch (error) {
        console.error('로컬 스토리지 저장 오류:', error);
    }
}

function loadFromLocalStorage(key) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : null;
    } catch (error) {
        console.error('로컬 스토리지 로드 오류:', error);
        return null;
    }
}

// 에러 핸들링
window.addEventListener('error', function(event) {
    console.error('JavaScript 오류:', event.error);
    showToast('예상치 못한 오류가 발생했습니다.', 'error');
});

// 온라인/오프라인 상태 감지
window.addEventListener('online', function() {
    showToast('인터넷 연결이 복구되었습니다.', 'success');
});

window.addEventListener('offline', function() {
    showToast('인터넷 연결이 끊어졌습니다.', 'warning');
});


// ==================== 운동 영상 관련 기능 ====================

// 운동 영상 검색
async function searchExerciseVideos(options = {}) {
    const {
        keyword = '',
        targetGroup = '',
        fitnessFactorName = '',
        exerciseTool = '',
        page = 0,
        size = 10
    } = options;
    
    try {
        const params = new URLSearchParams({
            page: page.toString(),
            size: size.toString()
        });
        
        if (keyword) params.append('keyword', keyword);
        if (targetGroup) params.append('target_group', targetGroup);
        if (fitnessFactorName) params.append('fitness_factor_name', fitnessFactorName);
        if (exerciseTool) params.append('exercise_tool', exerciseTool);
        
        const response = await apiCall(`/api/videos/search?${params.toString()}`);
        return response;
    } catch (error) {
        console.error('영상 검색 오류:', error);
        showToast('영상 검색 중 오류가 발생했습니다.', 'error');
        return null;
    }
}

// 근육별 영상 검색
async function searchVideosByMuscle(muscles, page = 0, size = 10) {
    try {
        const params = new URLSearchParams({
            page: page.toString(),
            size: size.toString()
        });
        
        muscles.forEach(muscle => params.append('muscles', muscle));
        
        const response = await apiCall(`/api/videos/by-muscle?${params.toString()}`);
        return response;
    } catch (error) {
        console.error('근육별 영상 검색 오류:', error);
        showToast('근육별 영상 검색 중 오류가 발생했습니다.', 'error');
        return null;
    }
}

// 인기 운동 영상 조회
async function getPopularVideos(targetGroup = '성인', limit = 10) {
    try {
        const params = new URLSearchParams({
            target_group: targetGroup,
            limit: limit.toString()
        });
        
        const response = await apiCall(`/api/videos/popular?${params.toString()}`);
        return response;
    } catch (error) {
        console.error('인기 영상 조회 오류:', error);
        showToast('인기 영상 조회 중 오류가 발생했습니다.', 'error');
        return null;
    }
}

// 향상된 추천 (영상 포함)
async function getEnhancedRecommendation(formData, includeVideos = true) {
    try {
        const params = includeVideos ? '?include_videos=true' : '?include_videos=false';
        
        const recommendation = await apiCall(`/api/recommend/enhanced${params}`, {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        return recommendation;
    } catch (error) {
        console.error('향상된 추천 생성 오류:', error);
        showToast('향상된 추천 생성 중 오류가 발생했습니다.', 'error');
        return null;
    }
}

// 외부 API 기반 추천 (새로운 메인 기능)
async function getExternalAPIRecommendation(formData) {
    try {
        const recommendation = await apiCall('/api/recommend/external', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        return recommendation;
    } catch (error) {
        console.error('외부 API 추천 생성 오류:', error);
        showToast('영상 기반 추천 생성 중 오류가 발생했습니다.', 'error');
        return null;
    }
}

// 사용자 맞춤 영상 추천
async function getUserVideoRecommendations(userId, options = {}) {
    const {
        targetGroup = '성인',
        exerciseTool = '',
        limit = 5
    } = options;
    
    try {
        const params = new URLSearchParams({
            target_group: targetGroup,
            limit: limit.toString()
        });
        
        if (exerciseTool) params.append('exercise_tool', exerciseTool);
        
        const response = await apiCall(`/api/videos/recommendations/${userId}?${params.toString()}`);
        return response;
    } catch (error) {
        console.error('맞춤 영상 추천 오류:', error);
        showToast('맞춤 영상 추천 중 오류가 발생했습니다.', 'error');
        return null;
    }
}

// 영상 카드 생성
function createVideoCard(video) {
    const card = document.createElement('div');
    card.className = 'col-lg-4 col-md-6 mb-4';
    
    const duration = video.videoLengthSeconds ? 
        `${Math.floor(video.videoLengthSeconds / 60)}:${(video.videoLengthSeconds % 60).toString().padStart(2, '0')}` : 'N/A';
    
    card.innerHTML = `
        <div class="card exercise-card h-100" onclick="showVideoDetail(${video.exerciseId})">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h5 class="card-title mb-0">${video.title}</h5>
                    <span class="badge bg-primary">${duration}</span>
                </div>
                
                ${video.targetGroup ? `<p class="text-muted small mb-2">대상: ${video.targetGroup}</p>` : ''}
                
                <div class="mb-3">
                    ${video.fitnessFactorName ? `<span class="badge bg-info me-2">${video.fitnessFactorName}</span>` : ''}
                    ${video.exerciseTool ? `<span class="badge bg-success">${video.exerciseTool}</span>` : ''}
                </div>
                
                <div class="text-center">
                    <button class="btn btn-outline-primary btn-sm" onclick="playVideo('${video.videoUrl}'); event.stopPropagation();">
                        <i class="fas fa-play"></i> 영상 보기
                    </button>
                </div>
                
                ${video.imageUrl ? `
                    <div class="mt-2">
                        <img src="${video.imageUrl}" class="img-fluid rounded" alt="${video.title}" style="max-height: 100px; width: 100%; object-fit: cover;">
                    </div>
                ` : ''}
            </div>
        </div>
    `;
    
    return card;
}

// 영상 상세 정보 모달
function showVideoDetail(videoId) {
    // 여기서는 간단한 alert로 처리하지만, 실제로는 상세 API 호출
    showToast(`영상 ID ${videoId}의 상세 정보를 표시합니다.`, 'info');
}

// 영상 재생
function playVideo(videoUrl) {
    if (!videoUrl) {
        showToast('영상 URL이 없습니다.', 'warning');
        return;
    }
    
    // 새 창에서 영상 재생
    window.open(videoUrl, '_blank');
}

// 영상 검색 결과 표시
function displayVideoResults(videos, containerId = 'videoResults') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = '';
    
    if (!videos || videos.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center py-5">
                <i class="fas fa-video-slash fa-3x text-muted mb-3"></i>
                <h4 class="text-muted">영상 결과가 없습니다</h4>
                <p class="text-muted">다른 검색 조건을 시도해보세요.</p>
            </div>
        `;
        return;
    }
    
    videos.forEach(video => {
        const card = createVideoCard(video);
        container.appendChild(card);
    });
}

// 향상된 추천 표시 (영상 포함)
function displayEnhancedRecommendation(recommendation) {
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
    
    // 기존 표시 함수 사용
    displayRecommendation(recommendation);
    
    // 영상 정보가 있는 경우 추가 표시
    let hasVideos = false;
    Object.values(recommendation.recommendation).forEach(day => {
        day.exercises.forEach(exercise => {
            if (exercise.video_url) {
                hasVideos = true;
            }
        });
    });
    
    if (hasVideos) {
        showToast('운동 영상 정보가 포함된 추천이 생성되었습니다!', 'success');
    }
}

// 추천 폼 제출 처리 업데이트 (영상 포함 옵션)
async function handleEnhancedRecommendSubmit(event, includeVideos = true) {
    // event.preventDefault();  // 버튼 클릭 이벤트에서는 preventDefault 불필요
    
    // 현재 클릭된 버튼 찾기 (event.target이 버튼 자체)
    const submitBtn = event.target || event.currentTarget;
    const originalText = submitBtn.innerHTML;
    
    try {
        // 로딩 상태 설정
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 생성 중...';
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
        
        // 향상된 추천 API 호출
        const recommendation = await getEnhancedRecommendation(formData, includeVideos);
        
        if (recommendation) {
            // 결과 표시
            displayEnhancedRecommendation(recommendation);
            
            showToast('운동 추천이 성공적으로 생성되었습니다!', 'success');
            
            // 결과 섹션으로 스크롤
            setTimeout(() => {
                document.getElementById('recommendationResult').scrollIntoView({
                    behavior: 'smooth'
                });
            }, 100);
        }
        
    } catch (error) {
        console.error('추천 생성 오류:', error);
        showToast('추천 생성 중 오류가 발생했습니다.', 'error');
    } finally {
        // 로딩 상태 해제
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}
