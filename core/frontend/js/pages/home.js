// Home Page
import { api } from '../api.js';
import { config } from '../config.js';

// Mock Data
const MOCK_ACHIEVEMENTS = [
    {
        image: 'https://www.figma.com/api/mcp/asset/612f37c2-02f1-499e-86b4-da086c6c3cf5',
        text: 'Студенты участвуют в проекте «Профессионалитет», получая навыки и гарантии трудоустройства от ведущих работодателей.'
    },
    {
        title: 'РЕСУРНЫЙ',
        titleSmall: 'ЦЕНТР',
        text: 'Признание как флагмана отрасли, оснащённого передовой технической базой для подготовки кадров'
    },
    {
        title: '90',
        titleSmall: 'лет',
        text: 'Мы создаём историю, растем вместе со страной и выпускаем специалистов, которые меняют мир к лучшему'
    }
];

const MOCK_SPECIALTIES = [
    {
        spec_code: '15.02.16',
        title: 'Технология машиностроения',
        img_path: 'images/'
    },
    {
        spec_code: '24.02.01',
        title: 'Производство летательных аппаратов',
        img_path: 'images/'
    },
    {
        spec_code: '24.02.02',
        title: 'Производство авиационных двигателей',
        img_path: 'images/'
    }
];

const MOCK_NEWS = [
    {
        id: 1,
        title: 'Название новости',
        text: 'Что случилось, где, когда и зачем? Что случилось, где, когда и зачем? Что случилось, где, когда и зачем?'
    },
    {
        id: 2,
        title: 'Название новости',
        text: 'Что случилось, где, когда и зачем? Что случилось, где, когда и зачем? Что случилось, где, когда и зачем?'
    },
    {
        id: 3,
        title: 'Название новости',
        text: 'Что случилось, где, когда и зачем? Что случилось, где, когда и зачем? Что случилось, где, когда и зачем?'
    }
];

function renderAchievements(achievements) {
    return `
        <section class="achievements">
            <div class="container">
                <h2 class="section-title">Достижения нашего колледжа</h2>
                <div class="grid grid-3">
                    ${achievements.map(achievement => `
                        <div class="achievement-card">
                            ${achievement.image ? `
                                <img src="${achievement.image}" alt="" class="achievement-card-image">
                            ` : `
                                <div class="achievement-card-title">
                                    ${achievement.title}
                                    ${achievement.titleSmall ? `<div class="achievement-card-title-small">${achievement.titleSmall}</div>` : ''}
                                </div>
                            `}
                            <div class="achievement-card-text">${achievement.text}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </section>
    `;
}

function renderSpecialties(specialties) {
    return `
        <section class="specialties">
            <div class="container">
                <h2 class="section-title">Специальности</h2>
                <div class="specialties-search">
                    <div class="specialties-search-input">
                        <input type="text" placeholder="Введите название специальности...">
                        <span class="specialties-search-icon">🔍</span>
                    </div>
                    <button onclick="window.location.href='/specialties'">
                        Показать больше
                    </button>
                </div>
                <div class="grid grid-3 specialties-grid">
                    ${specialties.map(specialty => {
                        // Склеиваем S3_BASE_URL с img_path, если путь есть
                        const imageUrl = specialty.img_path 
                            ? `${config.S3_BASE_URL}/${specialty.img_path}`.replace(/\/+/g, '/').replace(':/', '://')
                            : config.FALLBACK_IMAGE;
                        
                        return `
                            <div class="card specialty-card" onclick="window.location.href='/specialty/${specialty.spec_code}'">
                                <img 
                                    src="${imageUrl}" 
                                    alt="${specialty.title}" 
                                    class="card-image"
                                    onerror="this.src='${config.FALLBACK_IMAGE}'"
                                >
                                <div class="card-content">
                                    <h3 class="card-title">${specialty.title}</h3>
                                    <p class="card-meta">Код: ${specialty.spec_code}</p>
                                    <a href="/specialty/${specialty.spec_code}" class="card-link" onclick="event.stopPropagation()">
                                        Подробнее →
                                    </a>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        </section>
    `;
}

function renderNews(news) {
    return `
        <section class="news">
            <div class="container">
                <h2 class="section-title">Новости</h2>
                <div class="grid grid-3">
                    ${news.map(item => `
                        <div class="news-card">
                            <div>
                                <h3 class="news-card-title">${item.title}</h3>
                                <p class="news-card-text">${item.text}</p>
                            </div>
                            <a href="#/news/${item.id}" class="card-link">
                                Подробнее →
                            </a>
                        </div>
                    `).join('')}
                </div>
                <div class="show-more">
                    <button class="btn btn-secondary">Показать больше</button>
                </div>
            </div>
        </section>
    `;
}

export async function renderHomePage() {
    const content = document.getElementById('content');
    
    // Show loading state
    content.innerHTML = '<div class="container" style="text-align: center; padding: 4rem 0;"><div class="spinner"></div></div>';
    
    try {
        // Try to fetch real data (will use mocks if API fails)
        let specialties = MOCK_SPECIALTIES;
        
        try {
            specialties = await api.getSpecialties();
            specialties = specialties.slice(0, 3); // Take first 3
        } catch (error) {
            console.log('Using mock specialties data');
        }
        
        // Render page (without news section)
        content.innerHTML = `
            ${renderAchievements(MOCK_ACHIEVEMENTS)}
            ${renderSpecialties(specialties)}
        `;
        
    } catch (error) {
        console.error('Error rendering home page:', error);
        content.innerHTML = `
            <div class="container" style="text-align: center; padding: 4rem 0;">
                <p>Ошибка загрузки страницы</p>
            </div>
        `;
    }
}
