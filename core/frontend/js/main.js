// Main Application Entry Point
import { router } from './router.js';
import { initHeader } from './components/header.js';
import { initFooter } from './components/footer.js';
import { renderHomePage } from './pages/home.js';
import { renderSpecialtiesPage } from './pages/specialties.js';
import { renderSpecialtyPage } from './pages/specialty.js';
import { renderStudentsPage } from './pages/students.js';
import { renderApplicantsPage } from './pages/applicants.js';

// Global helper function to save specialty data to localStorage before navigation
window.saveAndNavigate = function(specId, specCode, title, imgPath) {
    console.log('saveAndNavigate called:', { specId, specCode, title, imgPath });
    const specialtyData = {
        spec_code: specCode,
        title: title,
        img_path: imgPath
    };
    localStorage.setItem(`specialty_${specId}`, JSON.stringify(specialtyData));
    console.log('Saved to localStorage:', `specialty_${specId}`, specialtyData);
    window.location.href = `/specialty/${specId}`;
};

// Initialize app
function init() {
    // Initialize header and footer
    initHeader();
    initFooter();
    
    // Register routes
    router.register('/', renderHomePage);
    router.register('/specialties', renderSpecialtiesPage);
    router.register('/students', renderStudentsPage);
    
    router.register('/specialty', (params) => {
        console.log('Specialty route called with params:', params);
        const specId = params[0];
        if (specId) {
            console.log('Rendering specialty page for ID:', specId);
            renderSpecialtyPage(specId);
        } else {
            console.log('No specId provided, redirecting to specialties');
            router.navigate('/specialties');
        }
    });
    
    router.register('/applicants', renderApplicantsPage);
    
    router.register('/methodists', () => {
        document.getElementById('content').innerHTML = `
            <div class="container" style="padding: 4rem 0;">
                <h1>Методистам</h1>
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
