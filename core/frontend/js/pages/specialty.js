// Specialty Detail Page
import { api } from '../api.js';
import { config } from '../config.js';
import { getIcon } from '../components/icons.js';

export async function renderSpecialtyPage(specId) {
    console.log('renderSpecialtyPage called with specId:', specId);
    const content = document.getElementById('content');
    
    // Show loading state
    content.innerHTML = '<div class="container" style="text-align: center; padding: 4rem 0;"><div class="spinner"></div></div>';
    
    try {
        // Check if we have cached basic data (spec_code, title, img_path)
        const cachedBasicData = localStorage.getItem(`specialty_${specId}`);
        const hasCache = !!cachedBasicData;
        
        console.log('Cache check:', { hasCache, cachedBasicData });
        
        let basicData = hasCache ? JSON.parse(cachedBasicData) : {};
        
        // Fetch detailed data from API
        // If we have cache, use lite=true (only description and details)
        // If no cache, use lite=false (full data including spec_code, title, img_path)
        console.log('Fetching specialty details with lite:', hasCache);
        const detailsData = await api.getSpecialtyDetails(specId, hasCache);
        console.log('Received details data:', detailsData);
        
        // Merge data: if lite=false, API returns everything; if lite=true, use cached basic data
        const specialty = {
            id: specId,
            spec_code: detailsData.spec_code || basicData.spec_code || 'N/A',
            title: detailsData.title || basicData.title || 'Специальность',
            img_path: detailsData.img_path || basicData.img_path || null,
            description: detailsData.description || 'Описание отсутствует',
            learn_years: detailsData.learn_years || 0,
            full_time: detailsData.full_time,
            free_form: detailsData.free_form,
            evening_form: detailsData.evening_form,
            cost_per_year: detailsData.cost_per_year || 0
        };
        
        const imageUrl = specialty.img_path 
            ? `${config.IMAGES_BASE}/${specialty.img_path}`.replace(/\/+/g, '/')
            : config.FALLBACK_IMAGE;
        
        // Format learn years
        const learnYearsText = formatLearnYears(specialty.learn_years);
        
        // Format cost/budget info
        const costInfo = formatCostInfo(specialty.free_form, specialty.cost_per_year);
        
        // Render page
        content.innerHTML = `
            <section class="specialty-detail">
                <div class="container">
                    <button class="back-button" onclick="window.history.back()">
                        <span class="back-icon">${getIcon('arrow')}</span>
                        <span>Назад к специальностям</span>
                    </button>
                    
                    <div class="specialty-content">
                        <div class="specialty-main">
                            <div class="specialty-left-column">
                                <div class="specialty-image-large">
                                    <img 
                                        src="${imageUrl}" 
                                        alt="${specialty.title}"
                                        onerror="this.src='${config.FALLBACK_IMAGE}'"
                                    >
                                </div>
                                
                                <div class="specialty-description-card">
                                    <div class="description-section">
                                        <h2>Описание специальности</h2>
                                        <p>${specialty.description}</p>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="specialty-info-card">
                                <div class="specialty-header">
                                    <h1 class="specialty-qualification">${specialty.title}</h1>
                                    <p class="specialty-code">Код: ${specialty.spec_code}</p>
                                </div>
                                
                                <div class="specialty-details">
                                    <div class="detail-item">
                                        <span class="detail-icon">${getIcon('time')}</span>
                                        <div class="detail-text">
                                            <p class="detail-label">Срок обучения</p>
                                            <p class="detail-value">${learnYearsText}</p>
                                        </div>
                                    </div>
                                    
                                    <div class="detail-item">
                                        <span class="detail-icon">${getIcon('group')}</span>
                                        <div class="detail-text">
                                            <p class="detail-label">Мест на группу</p>
                                            <p class="detail-value">25</p>
                                        </div>
                                    </div>
                                    
                                    <div class="detail-item">
                                        <span class="detail-icon">${getIcon('book')}</span>
                                        <div class="detail-text">
                                            <p class="detail-label">Форма обучения</p>
                                            <p class="detail-value">${specialty.full_time !== null ? 'Очная' : '—'}</p>
                                        </div>
                                    </div>
                                    
                                    <div class="detail-item">
                                        <span class="detail-icon">₽</span>
                                        <div class="detail-text">
                                            <p class="detail-label">Стоимость обучения</p>
                                            <p class="detail-value">${costInfo}</p>
                                        </div>
                                    </div>
                                </div>
                                
                                <a href="https://www.gosuslugi.ru/10171/1/form" target="_blank" class="btn btn-primary btn-apply">Подать документы</a>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        `;
        
    } catch (error) {
        console.error('Error rendering specialty page:', error);
        content.innerHTML = `
            <div class="container" style="text-align: center; padding: 4rem 0;">
                <p>Ошибка загрузки страницы</p>
                <button class="btn btn-primary" onclick="window.history.back()">Назад</button>
            </div>
        `;
    }
}

// Helper function to format learn years
function formatLearnYears(years) {
    if (!years || years === 0) return '—';
    
    // Вычитаем 1 год и добавляем 10 месяцев
    const fullYears = years - 1;
    const months = 10;
    
    // Если после вычитания получается 0 лет, показываем только месяцы
    if (fullYears === 0) {
        return `${months} месяцев`;
    }
    
    // Иначе показываем годы и месяцы
    const yearWord = fullYears === 1 ? 'год' : fullYears < 5 ? 'года' : 'лет';
    return `${fullYears} ${yearWord} ${months} месяцев`;
}

// Helper function to format cost/budget info
function formatCostInfo(freeForm, costPerYear) {
    // Если free_form = true, то "Бюджет или платно"
    if (freeForm === true) {
        return 'Бюджет или платно';
    }
    
    // Если free_form = false, то "Только платно"
    if (freeForm === false) {
        return 'Только платно';
    }
    
    // Если cost_per_year = 0, то "Только бюджет"
    if (costPerYear === 0) {
        return 'Только бюджет';
    }
    
    // Fallback
    return '—';
}
