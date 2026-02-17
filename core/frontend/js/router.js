// Simple SPA Router with History API
class Router {
    constructor() {
        this.routes = {};
        this.currentRoute = null;
        
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
    
    handleRoute() {
        const path = window.location.pathname;
        const [, route, ...params] = path.split('/').filter(Boolean);
        const routePath = '/' + (route || '');
        
        if (this.routes[routePath]) {
            this.currentRoute = routePath;
            this.routes[routePath](params);
        } else if (this.routes['*']) {
            this.routes['*']();
        } else {
            console.error('Route not found:', routePath);
        }
    }
    
    getParams() {
        const path = window.location.pathname;
        const parts = path.split('/').filter(Boolean);
        return parts.slice(1);
    }
}

export const router = new Router();
