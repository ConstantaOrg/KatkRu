// Main Application Entry Point
import { router } from './router.js';
import { initHeader } from './components/header.js';
import { initFooter } from './components/footer.js';
import { renderHomePage } from './pages/home.js';

// Initialize app
function init() {
    // Initialize header and footer
    initHeader();
    initFooter();
    
    // Register routes
    router.register('/', renderHomePage);
    
    // Placeholder routes (will be implemented later)
    router.register('/specialties', () => {
        document.getElementById('content').innerHTML = `
            <div class="container" style="padding: 4rem 0;">
                <h1>Специальности</h1>
                <p>Страница в разработке...</p>
            </div>
        `;
    });
    
    router.register('/specialty', () => {
        document.getElementById('content').innerHTML = `
            <div class="container" style="padding: 4rem 0;">
                <h1>Детали специальности</h1>
                <p>Страница в разработке...</p>
            </div>
        `;
    });
    
    router.register('/schedule', () => {
        document.getElementById('content').innerHTML = `
            <div class="container" style="padding: 4rem 0;">
                <h1>Расписание</h1>
                <p>Страница в разработке...</p>
            </div>
        `;
    });
    
    router.register('/applicants', () => {
        document.getElementById('content').innerHTML = `
            <div class="container" style="padding: 4rem 0;">
                <h1>Абитуриентам</h1>
                <p>Страница в разработке...</p>
            </div>
        `;
    });
    
    // 404 handler
    router.register('*', () => {
        document.getElementById('content').innerHTML = `
            <div class="container" style="padding: 4rem 0; text-align: center;">
                <h1>404</h1>
                <p>Страница не найдена</p>
                <a href="/" class="btn btn-primary" style="margin-top: 2rem;">На главную</a>
            </div>
        `;
    });
}

// Start app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
