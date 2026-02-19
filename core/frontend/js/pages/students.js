// Students Page - Schedule
import { api } from '../api.js';
import { getIcon } from '../components/icons.js';

let currentGroup = '';
let currentDate = '';
let autocompleteTimeout = null;

export async function renderStudentsPage() {
    const content = document.getElementById('content');
    
    // Get today's date in YYYY-MM-DD format
    const today = new Date();
    const todayStr = formatDateForAPI(today);
    const todayDisplay = formatDateForDisplay(today);
    currentDate = todayStr;
    
    content.innerHTML = `
        <section class="students-page">
            <div class="page-header">
                <div class="container">
                    <h1 class="page-title">Студентам</h1>
                    <p class="page-subtitle">Расписание занятий и документы</p>
                </div>
            </div>
            
            <div class="students-content">
                <!-- Filters Section -->
                <div class="filters-section">
                    <div class="filters-header">
                        <span class="filters-icon">${getIcon('filter')}</span>
                        <h2>Фильтры</h2>
                    </div>
                    
                    <div class="filters-controls">
                        <div class="filter-group">
                            <label for="group-input">По группе</label>
                            <div class="filter-input-wrapper">
                                <input 
                                    type="text" 
                                    id="group-input" 
                                    class="filter-input" 
                                    placeholder="Выберите группу"
                                    value="${currentGroup}"
                                    autocomplete="off"
                                >
                                <div class="autocomplete-dropdown" id="group-autocomplete"></div>
                            </div>
                        </div>
                        
                        <div class="filter-group">
                            <label for="date-input">По дате</label>
                            <input 
                                type="date" 
                                id="date-input" 
                                class="filter-input" 
                                value="${todayStr}"
                            >
                        </div>
                        
                        <div class="filter-group">
                            <button class="btn-reset-filters" id="reset-filters-btn">
                                Сбросить фильтры
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Schedule Section -->
                <div class="schedule-section">
                    <div class="schedule-header">
                        <span class="schedule-icon">${getIcon('timetable')}</span>
                        <h2>Расписание занятий</h2>
                    </div>
                    
                    <div id="schedule-results">
                        <p class="no-schedule">Результатов нет</p>
                    </div>
                </div>
            </div>
        </section>
    `;
    
    // Attach event listeners
    attachEventListeners();
    updateResetButtonState();
}

function attachEventListeners() {
    const groupInput = document.getElementById('group-input');
    const dateInput = document.getElementById('date-input');
    const resetBtn = document.getElementById('reset-filters-btn');
    const autocompleteDropdown = document.getElementById('group-autocomplete');
    
    // Group input - autocomplete with debounce
    groupInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.trim();
        
        // Clear previous timeout
        if (autocompleteTimeout) {
            clearTimeout(autocompleteTimeout);
        }
        
        // Hide dropdown if less than 1 character
        if (searchTerm.length < 1) {
            autocompleteDropdown.classList.remove('active');
            return;
        }
        
        // Debounce 300ms
        autocompleteTimeout = setTimeout(async () => {
            try {
                const results = await api.searchGroups(searchTerm);
                showAutocomplete(results);
            } catch (error) {
                console.error('Autocomplete error:', error);
                autocompleteDropdown.classList.remove('active');
            }
        }, 300);
    });
    
    // Ignore service keys
    groupInput.addEventListener('keydown', (e) => {
        const serviceKeys = ['Shift', 'Control', 'Alt', 'Meta', 'CapsLock', 'Tab', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'];
        if (serviceKeys.includes(e.key)) {
            return;
        }
        
        // Close dropdown on Escape
        if (e.key === 'Escape') {
            autocompleteDropdown.classList.remove('active');
        }
    });
    
    // Close autocomplete on click outside
    document.addEventListener('click', (e) => {
        if (!groupInput.contains(e.target) && !autocompleteDropdown.contains(e.target)) {
            autocompleteDropdown.classList.remove('active');
        }
    });
    
    // Date input - trigger search on change
    dateInput.addEventListener('change', () => {
        const newDate = dateInput.value;
        const todayStr = formatDateForAPI(new Date());
        
        // Update currentDate only if it's different from today
        if (newDate !== todayStr) {
            currentDate = newDate;
        } else {
            currentDate = todayStr;
        }
        
        updateResetButtonState();
        
        if (currentGroup) {
            loadSchedule();
        }
    });
    
    // Reset filters
    resetBtn.addEventListener('click', () => {
        currentGroup = '';
        currentDate = formatDateForAPI(new Date());
        groupInput.value = '';
        dateInput.value = currentDate;
        autocompleteDropdown.classList.remove('active');
        
        const scheduleResults = document.getElementById('schedule-results');
        scheduleResults.innerHTML = '<p class="no-schedule">Результатов нет</p>';
        
        updateResetButtonState();
    });
}

function showAutocomplete(results) {
    const autocompleteDropdown = document.getElementById('group-autocomplete');
    
    if (!results || results.length === 0) {
        autocompleteDropdown.classList.remove('active');
        return;
    }
    
    autocompleteDropdown.innerHTML = results.map(item => `
        <div class="autocomplete-item" data-group="${item.group_name}">
            <span class="autocomplete-title">${item.group_name}</span>
        </div>
    `).join('');
    
    autocompleteDropdown.classList.add('active');
    
    // Add click handlers to autocomplete items
    const items = autocompleteDropdown.querySelectorAll('.autocomplete-item');
    items.forEach(item => {
        item.addEventListener('click', () => {
            const groupName = item.dataset.group;
            const groupInput = document.getElementById('group-input');
            
            groupInput.value = groupName;
            currentGroup = groupName;
            autocompleteDropdown.classList.remove('active');
            
            updateResetButtonState();
            
            // Immediately load schedule when group is selected
            loadSchedule();
        });
    });
}

function updateResetButtonState() {
    const resetBtn = document.getElementById('reset-filters-btn');
    const todayStr = formatDateForAPI(new Date());
    
    // Check if any filters are active
    const hasActiveFilters = currentGroup !== '' || currentDate !== todayStr;
    
    if (hasActiveFilters) {
        resetBtn.style.backgroundColor = 'var(--color-primary)';
        resetBtn.style.color = 'white';
        resetBtn.disabled = false;
    } else {
        resetBtn.style.backgroundColor = '#EBEDF0';
        resetBtn.style.color = '#000000';
        resetBtn.disabled = false; // Keep enabled but gray
    }
}

async function loadSchedule() {
    const scheduleResults = document.getElementById('schedule-results');
    
    if (!currentGroup) {
        scheduleResults.innerHTML = '<p class="no-schedule">Введите номер группы</p>';
        return;
    }
    
    // Show loading
    scheduleResults.innerHTML = '<p class="no-schedule">Загрузка...</p>';
    
    try {
        const schedule = await api.getSchedule(currentGroup, currentDate);
        
        if (!schedule || schedule.length === 0) {
            scheduleResults.innerHTML = '<p class="no-schedule">Результатов нет</p>';
            return;
        }
        
        // Render schedule table
        renderScheduleTable(schedule);
        
    } catch (error) {
        console.error('Error loading schedule:', error);
        scheduleResults.innerHTML = '<p class="no-schedule">Ошибка загрузки расписания</p>';
    }
}

function renderScheduleTable(schedule) {
    const scheduleResults = document.getElementById('schedule-results');
    
    const tableHTML = `
        <div class="schedule-table-wrapper">
            <div class="schedule-table-header">
                <div class="schedule-col-position">Номер пары</div>
                <div class="schedule-col-aud">Аудитория</div>
                <div class="schedule-col-subject">Предмет</div>
                <div class="schedule-col-teacher">Преподаватель</div>
            </div>
            ${schedule.map(item => `
                <div class="schedule-table-row">
                    <div class="schedule-col-position">${item.position || '—'}</div>
                    <div class="schedule-col-aud">${item.aud || '—'}</div>
                    <div class="schedule-col-subject">${item.title || '—'}</div>
                    <div class="schedule-col-teacher">${item.fio || '—'}</div>
                </div>
            `).join('')}
        </div>
    `;
    
    scheduleResults.innerHTML = tableHTML;
}

// Helper function to format date for API (YYYY-MM-DD)
function formatDateForAPI(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// Helper function to format date for display (DD.MM.YYYY, День недели)
function formatDateForDisplay(date) {
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    
    const weekdays = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'];
    const weekday = weekdays[date.getDay()];
    
    return `${day}.${month}.${year}, ${weekday}`;
}

