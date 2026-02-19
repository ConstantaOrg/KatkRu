// Simple SPA Router with History API
class Router {
    constructor() {
        this.routes = {};
        this.currentRoute = null;
        this.isHandling = false; // Флаг для предотвращения двойного вызова
        
        // Use History API instead of hash
        window.addEventListener('popstate', () => this.handleRoute());
        window.addEventListener('load', () => this.handleRoute());
        
        // Intercept all link clicks
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href^="/"]');
            if (link && !link.hasAttribute('target')) {
                e.preventDefault();
                this.navigate(link.getAttribute('href'));
            }
        });
    }
    
    register(path, handler) {
        this.routes[path] = handler;
    }
    
    navigate(path) {
        window.history.pushState({}, '', path);
        this.handleRoute();
    }
    
    async handleRoute() {
        // Предотвращаем двойной вызов
        if (this.isHandling) {
            console.log('Router: already handling, skipping');
            return;
        }
        
        this.isHandling = true;
        
        const path = window.location.pathname;
        console.log('Router: handling path:', path);
        
        // Правильный парсинг пути
        const parts = path.split('/').filter(Boolean);
        console.log('Router: path parts:', parts);
        
        // Если путь пустой - это главная, иначе берем первую часть
        const routePath = parts.length === 0 ? '/' : '/' + parts[0];
        const params = parts.slice(1);
        
        console.log('Router: parsed route:', routePath);
        console.log('Router: params:', params);
        console.log('Router: available routes:', Object.keys(this.routes));
        
        try {
            if (this.routes[routePath]) {
                console.log('Router: found route handler for:', routePath);
                this.currentRoute = routePath;
                await this.routes[routePath](params);
            } else if (this.routes['*']) {
                console.log('Router: using 404 handler');
                await this.routes['*']();
            } else {
                console.error('Route not found:', routePath);
            }
        } finally {
            this.isHandling = false;
        }
    }
    
    getParams() {
        const path = window.location.pathname;
        const parts = path.split('/').filter(Boolean);
        return parts.slice(1);
    }
}

export const router = new Router();
