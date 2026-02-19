// Specialties Page
import { api } from '../api.js';
import { config } from '../config.js';
import { getIcon } from '../components/icons.js';

let currentOffset = 0;
const LIMIT = 9; // Показываем по 9 карточек
let currentSearchTerm = '';
let isSearchMode = false;

export async function renderSpecialtiesPage() {
    const content = document.getElementById('content');
    
    // Show loading state
    content.innerHTML = '<div class="container" style="text-align: center; padding: 4rem 0;"><div class="spinner"></div></div>';
    
    try {
        // Reset state
        currentOffset = 0;
        currentSearchTerm = '';
        isSearchMode = false;
        
        // Fetch specialties
        const specialties = await api.getSpecialties(LIMIT, currentOffset);
        
        // Render page
        content.innerHTML = `
            <section class="specialties-hero">
                <h1 class="specialties-hero-title">Выбери свою профессию</h1>
                <p class="specialties-hero-subtitle">Современные специальности для успешного будущего</p>
            </section>
            
            <section class="specialties-page">
                <div class="container">
                    <div class="specialties-page-search">
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
                    </div>
                    
                    <div class="grid grid-3 specialties-page-grid" id="specialties-grid">
                        ${renderSpecialtyCards(specialties)}
                    </div>
                    
                    ${specialties.length >= LIMIT ? `
                        <div class="show-more">
                            <button class="btn btn-primary" id="load-more-btn">Показать больше</button>
                        </div>
                    ` : ''}
                </div>
            </section>
        `;
        
        // Initialize search and load more
        initSpecialtiesSearch();
        initLoadMore();
        
    } catch (error) {
        console.error('Error rendering specialties page:', error);
        content.innerHTML = `
            <div class="container" style="text-align: center; padding: 4rem 0;">
                <p>Ошибка загрузки страницы</p>
            </div>
        `;
    }
}

function renderSpecialtyCards(specialties) {
    if (specialties.length === 0) {
        return '<p class="no-results">Ничего не найдено</p>';
    }
    
    return specialties.map(specialty => {
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
}

// Search functionality
let searchDebounceTimer = null;

function initSpecialtiesSearch() {
    const searchInput = document.getElementById('specialty-search-input');
    const dropdown = document.getElementById('autocomplete-dropdown');
    
    if (!searchInput || !dropdown) return;
    
    const ignoredKeys = ['Control', 'Shift', 'Alt', 'Meta', 'CapsLock', 'Tab', 
                         'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'];
    
    // Prevent form submission
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            return false;
        }
    });
    
    // Handle Enter for search
    searchInput.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            e.stopPropagation();
            const searchTerm = searchInput.value.trim();
            if (searchTerm.length >= 2) {
                await performSearch(searchTerm);
            }
            closeAutocomplete();
            return false;
        }
        
        if (e.key === 'Escape') {
            closeAutocomplete();
            return;
        }
        
        if (ignoredKeys.includes(e.key)) {
            return;
        }
    });
    
    // Autocomplete on input
    searchInput.addEventListener('input', async (e) => {
        const value = e.target.value.trim();
        
        clearTimeout(searchDebounceTimer);
        
        if (value.length < 2) {
            closeAutocomplete();
            return;
        }
        
        searchDebounceTimer = setTimeout(async () => {
            await showAutocomplete(value);
        }, 300);
    });
    
    // Close on click outside
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
    if (!searchTerm || searchTerm.length < 2) return;
    
    const grid = document.getElementById('specialties-grid');
    const loadMoreBtn = document.getElementById('load-more-btn');
    
    if (!grid) return;
    
    try {
        grid.innerHTML = '<div class="spinner"></div>';
        
        // Search mode
        isSearchMode = true;
        currentSearchTerm = searchTerm;
        currentOffset = 0;
        
        const results = await api.searchSpecialties(searchTerm, LIMIT, currentOffset);
        
        grid.innerHTML = renderSpecialtyCards(results);
        
        // Show/hide load more button
        if (loadMoreBtn) {
            if (results.length >= LIMIT) {
                loadMoreBtn.style.display = 'block';
            } else {
                loadMoreBtn.style.display = 'none';
            }
        }
        
    } catch (error) {
        console.error('Search error:', error);
        grid.innerHTML = '<p class="no-results">Ошибка поиска. Попробуйте еще раз.</p>';
    }
}

function initLoadMore() {
    const loadMoreBtn = document.getElementById('load-more-btn');
    if (!loadMoreBtn) return;
    
    loadMoreBtn.addEventListener('click', async () => {
        const grid = document.getElementById('specialties-grid');
        if (!grid) return;
        
        try {
            loadMoreBtn.disabled = true;
            loadMoreBtn.textContent = 'Загрузка...';
            
            currentOffset += LIMIT;
            
            let newSpecialties;
            if (isSearchMode && currentSearchTerm) {
                newSpecialties = await api.searchSpecialties(currentSearchTerm, LIMIT, currentOffset);
            } else {
                newSpecialties = await api.getSpecialties(LIMIT, currentOffset);
            }
            
            if (newSpecialties.length > 0) {
                grid.innerHTML += renderSpecialtyCards(newSpecialties);
            }
            
            // Hide button if no more results
            if (newSpecialties.length < LIMIT) {
                loadMoreBtn.style.display = 'none';
            } else {
                loadMoreBtn.disabled = false;
                loadMoreBtn.textContent = 'Показать больше';
            }
            
        } catch (error) {
            console.error('Load more error:', error);
            loadMoreBtn.disabled = false;
            loadMoreBtn.textContent = 'Показать больше';
        }
    });
}
