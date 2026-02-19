// Applicants Page - Information for prospective students
import { getIcon } from '../components/icons.js';

export async function renderApplicantsPage() {
    const content = document.getElementById('content');
    
    content.innerHTML = `
        <section class="applicants-page">
            <div class="page-header">
                <div class="container">
                    <h1 class="page-title">Абитуриентам</h1>
                    <p class="page-subtitle">Информация для поступающих</p>
                </div>
            </div>
            
            <div class="applicants-content">
                <!-- Left Column: Documents and Scores -->
                <div class="applicants-left">
                    <!-- Required Documents Section -->
                    <div class="documents-section">
                        <div class="section-header">
                            <span class="section-icon">${getIcon('document')}</span>
                            <h2>Необходимые документы и справки</h2>
                        </div>
                        
                        <div class="documents-list">
                            ${renderDocumentItem('Заявление', 'скачать бланк заявления', 'https://edu.tatar.ru/upload/storage/org6234/files/заявление%20бланк_A4_400.doc')}
                            ${renderDocumentItem('Анкета абитуриента', 'скачать анкету абитуриента', 'https://edu.tatar.ru/upload/storage/org6234/files/Анкета%20абитуриента_A4_400.doc')}
                            ${renderDocumentItem('Электронное заявление на сайте', 'сайт: uslugi.tatarstan.ru', 'https://uslugi.tatarstan.ru')}
                            ${renderDocumentItem('Аттестат об основном общем образовании', 'Оригинал или копия')}
                            ${renderDocumentItem('Паспорт', '3 шт, страницы 2,3,5')}
                            ${renderDocumentItem('ИНН', 'Копия, 4 шт')}
                            ${renderDocumentItem('Фотографии', '3*4 см, 4 шт')}
                            ${renderDocumentItem('Медицинская справка', 'Форма 086/у')}
                            ${renderDocumentItem('СНИЛС', 'Копия, 3 шт')}
                            ${renderDocumentItem('Приписное свидетельство', 'Форма 025/у. Юношам (мужчинам) до 2008 года рождения при поступлении необходимо предоставить копию приписного удостоверения (копию военного билета) или справку воекномата о воинском учете.')}
                            ${renderDocumentItem('Медицинский полис', 'Копия, 3 шт')}
                            ${renderDocumentItem('Медицинская карта', '26 форма')}
                            ${renderDocumentItem('Карта профилактических прививок', '63 форма')}
                            ${renderDocumentItem('Характеристика из школы', 'Оригинал')}
                            ${renderDocumentItem('Справка о здоровье', 'Психиатр, нарколог')}
                            ${renderDocumentItemWithList('Один из трех медицинских документов, указанных ниже', [
                                'Флюорография (с 17 лет свежая ФЛГ 2024г)',
                                'До 17 лет свежий Диаскинтест, справка о результатах пробы',
                                'Если нет ФЛГ и Диаскинтеста - нужна справка от фтизиатра, об отсутствии туберкулёза'
                            ])}
                        </div>
                    </div>
                    
                    <!-- Competition Lists Section -->
                    <div class="competition-section">
                        <div class="section-header">
                            <span class="section-icon">${getIcon('group')}</span>
                            <h2>Конкурсные списки 2026</h2>
                        </div>
                        
                        <p class="competition-text">
                            Ознакомиться со списками можно ознакомиться в <a href="https://vk.com/club215705671" target="_blank" class="link-primary">нашем сообществе ВКонтакте</a>
                        </p>
                    </div>
                </div>
                
                <!-- Right Column: Important Dates -->
                <div class="applicants-right">
                    <div class="dates-section">
                        <div class="section-header">
                            <span class="section-icon">${getIcon('timetable')}</span>
                            <h2>Важные даты</h2>
                        </div>
                        
                        <div class="dates-list">
                            ${renderDateItem('Начало приема документов', '20 июня 2026')}
                            ${renderDateItem('Окончание приема (бюджет)', '15 августа 2026')}
                            ${renderDateItem('Публикация списков', '17 августа 2026')}
                            ${renderDateItem('Начало занятий', '1 сентября 2026')}
                        </div>
                        
                        <div class="contacts-section">
                            <h3>Контакты приемной комиссии</h3>
                            
                            <div class="contact-item">
                                <span class="contact-icon">${getIcon('phoneGray')}</span>
                                <div class="contact-text">
                                    <p class="contact-value">+7(843) 571-35-30</p>
                                </div>
                            </div>
                            
                            <div class="contact-item">
                                <span class="contact-icon">${getIcon('emailGray')}</span>
                                <div class="contact-text">
                                    <p class="contact-value">pk@kaviat.ru</p>
                                </div>
                            </div>
                            
                            <div class="contact-item">
                                <span class="contact-icon">${getIcon('timeGray')}</span>
                                <div class="contact-text">
                                    <p class="contact-value">Пн-Пт 09:00 - 18:00</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    `;
}

function renderDocumentItem(title, description, link = null) {
    const linkHtml = link ? `<a href="${link}" target="_blank" class="document-link">${description}</a>` : `<p class="document-description">${description}</p>`;
    
    return `
        <div class="document-item">
            <span class="document-bullet"></span>
            <div class="document-content">
                <p class="document-title">${title}</p>
                ${linkHtml}
            </div>
        </div>
    `;
}

function renderDocumentItemWithList(title, items) {
    const listHtml = `
        <ul class="document-list">
            ${items.map(item => `<li>${item}</li>`).join('')}
        </ul>
    `;
    
    return `
        <div class="document-item">
            <span class="document-bullet"></span>
            <div class="document-content">
                <p class="document-title">${title}</p>
                ${listHtml}
            </div>
        </div>
    `;
}

function renderDateItem(label, date) {
    return `
        <div class="date-item">
            <p class="date-label">${label}</p>
            <p class="date-value">${date}</p>
        </div>
    `;
}
