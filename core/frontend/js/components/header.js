// Header Component
import { config } from '../config.js';

export function renderHeader() {
    const logoUrl = 'https://www.figma.com/api/mcp/asset/593ba6dd-7094-487f-a21f-7a6740a90eb3';
    
    return `
        <header class="header">
            <div class="container header-content">
                <a href="/" class="header-logo">
                    <img src="${logoUrl}" alt="Логотип" class="header-logo-image">
                    <div class="header-logo-text">
                        <h1>${config.APP_NAME}</h1>
                        <p>${config.APP_TAGLINE}</p>
                    </div>
                </a>
                <nav class="header-nav">
                    <a href="/" data-route="/">О нас</a>
                    <a href="/specialties" data-route="/specialties">Специальности</a>
                    <a href="/schedule" data-route="/schedule">Студентам</a>
                    <a href="/applicants" data-route="/applicants">Абитуриентам</a>
                </nav>
            </div>
        </header>
    `;
}

export function initHeader() {
    const headerEl = document.getElementById('header');
    if (headerEl) {
        headerEl.innerHTML = renderHeader();
        updateActiveLink();
        
        // Update active link on route change
        window.addEventListener('popstate', updateActiveLink);
    }
}

function updateActiveLink() {
    const path = window.location.pathname;
    const links = document.querySelectorAll('.header-nav a');
    
    links.forEach(link => {
        const route = link.getAttribute('data-route');
        if (path === route || (route !== '/' && path.startsWith(route))) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}
