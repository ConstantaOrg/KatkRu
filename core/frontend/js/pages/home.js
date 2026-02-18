// Home Page
import { api } from '../api.js';
import { config } from '../config.js';
import { getIcon } from '../components/icons.js';

// Mock Data
const MOCK_ACHIEVEMENTS = [
    {
        image: '/images/professionalitet.png',
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

function renderSpecialties(specialties, isSearchResult = false) {
    const searchTitle = isSearchResult ? 'Результаты поиска' : 'Специальности';
    
    return `
        <section class="specialties">
            <div class="container">
                <h2 class="section-title">${searchTitle}</h2>
                <div class="specialties-search">
                    <div class="specialties-search-wrapper">
                        <div class="specialties-search-input">
                            <input 
                                type="text" 
                                id="specialty-search-input"
                                placeholder="Введите название специальности..."
                                autocomplete="off"
                            >
                            <span class="specialties-search-icon">${getIcon('search')}</span>
                        </div>
                        <div class="autocomplete-dropdown" id="autocomplete-dropdown"></div>
                    </div>
                    <button onclick="window.location.href='/specialties'">
                        Показать больше
                    </button>
                </div>
                <div class="grid grid-3 specialties-grid">
                    ${specialties.length > 0 ? specialties.map(specialty => {
                        // Строим путь к изображению
                        const imageUrl = specialty.img_path 
                            ? `${config.IMAGES_BASE}/${specialty.img_path}`.replace(/\/+/g, '/')
                            : config.FALLBACK_IMAGE;
                        
                        return `
                            <div class="card specialty-card" onclick="saveAndNavigate('${specialty.id}', '${specialty.spec_code}', '${specialty.title.replace(/'/g, "\\'")}', '${specialty.img_path || ''}')">
                                <img 
                                    src="${imageUrl}" 
                                    alt="${specialty.title}" 
                                    class="card-image"
                                    onerror="this.src='${config.FALLBACK_IMAGE}'"
                                >
                                <div class="card-content">
                                    <h3 class="card-title">${specialty.title}</h3>
                                    <p class="card-meta">Код: ${specialty.spec_code}</p>
                                    <a href="/specialty/${specialty.id}" class="card-link" onclick="event.stopPropagation(); saveAndNavigate('${specialty.id}', '${specialty.spec_code}', '${specialty.title.replace(/'/g, "\\'")}', '${specialty.img_path || ''}')">
                                        Подробнее →
                                    </a>
                                </div>
                            </div>
                        `;
                    }).join('') : '<p class="no-results">Ничего не найдено</p>'}
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
            specialties = await api.getSpecialties(3, 0);
        } catch (error) {
            console.log('Using mock specialties data');
        }
        
        // Render page (without news section)
        content.innerHTML = `
            ${renderAchievements(MOCK_ACHIEVEMENTS)}
            ${renderSpecialties(specialties, false)}
        `;
        
        console.log('Home page rendered, initializing search...');
        
        // Initialize search functionality
        initSearch();
        
        console.log('Search initialized');
        
    } catch (error) {
        console.error('Error rendering home page:', error);
        content.innerHTML = `
            <div class="container" style="text-align: center; padding: 4rem 0;">
                <p>Ошибка загрузки страницы</p>
            </div>
        `;
    }
}

// Search functionality
let searchDebounceTimer = null;
let currentSearchTerm = '';

function initSearch() {
    console.log('initSearch called');
    
    const searchInput = document.getElementById('specialty-search-input');
    const dropdown = document.getElementById('autocomplete-dropdown');
    
    console.log('Search input:', searchInput);
    console.log('Dropdown:', dropdown);
    
    if (!searchInput || !dropdown) {
        console.error('Search elements not found!');
        return;
    }
    
    console.log('Adding event listeners...');
    
    // Служебные клавиши, которые игнорируем
    const ignoredKeys = ['Control', 'Shift', 'Alt', 'Meta', 'CapsLock', 'Tab', 
                         'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'];
    
    // Предотвращаем отправку формы при Enter
    searchInput.addEventListener('keypress', (e) => {
        console.log('keypress event:', e.key);
        if (e.key === 'Enter') {
            console.log('Enter pressed - preventing default');
            e.preventDefault();
            return false;
        }
    });
    
    // Обработка ввода с debounce
    searchInput.addEventListener('keydown', async (e) => {
        console.log('keydown event:', e.key);
        
        // Enter - выполняем поиск
        if (e.key === 'Enter') {
            console.log('Enter in keydown - performing search');
            e.preventDefault();
            e.stopPropagation();
            const searchTerm = searchInput.value.trim();
            console.log('Search term:', searchTerm);
            if (searchTerm.length >= 2) {
                await performSearch(searchTerm);
            } else {
                console.log('Search term too short');
            }
            closeAutocomplete();
            return false;
        }
        
        // Escape - закрываем автокомплит
        if (e.key === 'Escape') {
            closeAutocomplete();
            return;
        }
        
        // Игнорируем служебные клавиши
        if (ignoredKeys.includes(e.key)) {
            return;
        }
    });
    
    console.log('Event listeners added');
    
    searchInput.addEventListener('input', async (e) => {
        const value = e.target.value.trim();
        currentSearchTerm = value;
        
        // Очищаем предыдущий таймер
        clearTimeout(searchDebounceTimer);
        
        // Если меньше 2 символов - закрываем автокомплит
        if (value.length < 2) {
            closeAutocomplete();
            return;
        }
        
        // Запускаем новый таймер
        searchDebounceTimer = setTimeout(async () => {
            await showAutocomplete(value);
        }, 300);
    });
    
    // Закрытие при клике вне поля
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
            closeAutocomplete();
        }
    });
}

async function showAutocomplete(searchTerm) {
    const dropdown = document.getElementById('autocomplete-dropdown');
    if (!dropdown) return;
    
    try {
        const results = await api.autocompleteSpecialties(searchTerm);
        
        if (results.length === 0) {
            closeAutocomplete();
            return;
        }
        
        // Формируем HTML для выпадающего списка
        dropdown.innerHTML = results.map(item => {
            const displayText = `${item.spec_code} ${item.title}`;
            return `
                <div class="autocomplete-item" data-value="${displayText}">
                    <span class="autocomplete-code">${item.spec_code}</span>
                    <span class="autocomplete-title">${item.title}</span>
                </div>
            `;
        }).join('');
        
        dropdown.classList.add('active');
        
        // Обработка клика по элементу
        dropdown.querySelectorAll('.autocomplete-item').forEach(item => {
            item.addEventListener('click', () => {
                const searchInput = document.getElementById('specialty-search-input');
                const value = item.getAttribute('data-value');
                searchInput.value = value;
                closeAutocomplete();
                // Возвращаем фокус на поле ввода
                searchInput.focus();
            });
        });
        
    } catch (error) {
        console.error('Autocomplete error:', error);
        closeAutocomplete();
    }
}

function closeAutocomplete() {
    const dropdown = document.getElementById('autocomplete-dropdown');
    if (dropdown) {
        dropdown.classList.remove('active');
        dropdown.innerHTML = '';
    }
}

async function performSearch(searchTerm) {
    if (!searchTerm || searchTerm.length < 2) {
        console.log('Search term too short:', searchTerm);
        return;
    }
    
    console.log('Performing search for:', searchTerm);
    
    const specialtiesSection = document.querySelector('.specialties');
    if (!specialtiesSection) {
        console.error('Specialties section not found');
        return;
    }
    
    try {
        // Показываем загрузку
        const grid = specialtiesSection.querySelector('.specialties-grid');
        grid.innerHTML = '<div class="spinner"></div>';
        
        console.log('Calling API searchSpecialties...');
        
        // Выполняем поиск
        const results = await api.searchSpecialties(searchTerm, 6, 0);
        
        console.log('Search results:', results);
        
        // Обновляем заголовок и результаты
        const title = specialtiesSection.querySelector('.section-title');
        title.textContent = 'Результаты поиска';
        
        // Рендерим результаты
        if (results.length > 0) {
            grid.innerHTML = results.map(specialty => {
                const imageUrl = specialty.img_path 
                    ? `${config.IMAGES_BASE}/${specialty.img_path}`.replace(/\/+/g, '/')
                    : config.FALLBACK_IMAGE;
                
                return `
                    <div class="card specialty-card" onclick="saveAndNavigate('${specialty.id}', '${specialty.spec_code}', '${specialty.title.replace(/'/g, "\\'")}', '${specialty.img_path || ''}')">
                        <img 
                            src="${imageUrl}" 
                            alt="${specialty.title}" 
                            class="card-image"
                            onerror="this.src='${config.FALLBACK_IMAGE}'"
                        >
                        <div class="card-content">
                            <h3 class="card-title">${specialty.title}</h3>
                            <p class="card-meta">Код: ${specialty.spec_code}</p>
                            <a href="/specialty/${specialty.id}" class="card-link" onclick="event.stopPropagation(); saveAndNavigate('${specialty.id}', '${specialty.spec_code}', '${specialty.title.replace(/'/g, "\\'")}', '${specialty.img_path || ''}')">
                                Подробнее →
                            </a>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            grid.innerHTML = '<p class="no-results">Ничего не найдено</p>';
        }
        
    } catch (error) {
        console.error('Search error:', error);
        const grid = specialtiesSection.querySelector('.specialties-grid');
        grid.innerHTML = '<p class="no-results">Ошибка поиска. Попробуйте еще раз.</p>';
    }
}
