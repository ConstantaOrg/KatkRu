// API Client
import { config } from './config.js';

class ApiClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
    
    // Specialties
    async getSpecialties(limit = 6, offset = 0) {
        const response = await this.request('/v1/public/specialties/all', {
            method: 'POST',
            body: JSON.stringify({
                limit: limit,
                offset: offset
            })
        });
        
        return response.specialties || [];
    }
    
    // Autocomplete for specialties
    async autocompleteSpecialties(searchTerm) {
        const response = await this.request('/v1/public/elastic/autocomplete_spec', {
            method: 'POST',
            body: JSON.stringify({
                search_term: searchTerm
            })
        });
        
        return response.search_res || [];
    }
    
    // Full-text search for specialties
    async searchSpecialties(searchTerm, limit = 6, offset = 0) {
        const response = await this.request('/v1/public/elastic/ext_spec', {
            method: 'POST',
            body: JSON.stringify({
                body: {
                    search_term: searchTerm
                },
                pagen: {
                    offset: offset,
                    limit: limit
                }
            })
        });
        
        return response.search_res || [];
    }
    
    // Get specialty details by ID
    async getSpecialtyDetails(specId, lite = false) {
        const response = await this.request(`/v1/public/specialties/${specId}?lite=${lite}`);
        return response.speciality || null;
    }
    
    // Schedule - get timetable for a group on a specific date
    async getSchedule(group, date) {
        const response = await this.request('/v1/public/ttable/get', {
            method: 'POST',
            body: JSON.stringify({
                group: group.toUpperCase(), // Convert to uppercase
                date: date // Format: YYYY-MM-DD
            })
        });
        
        return response.schedule || [];
    }
    
    // Search groups - autocomplete for group names
    async searchGroups(searchTerm) {
        const response = await this.request('/v1/public/elastic/search_group', {
            method: 'POST',
            body: JSON.stringify({
                search_term: searchTerm
            })
        });
        
        return response.search_res || [];
    }
    
    // News (if exists)
    async getNews(limit = 3) {
        return this.request(`/news?limit=${limit}`);
    }
}

export const api = new ApiClient(config.API_BASE);
