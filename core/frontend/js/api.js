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
    async getSpecialties(search = '', limit = 6, offset = 0) {
        const response = await this.request('/v1/public/specialties/all', {
            method: 'POST',
            body: JSON.stringify({
                limit: limit,
                offset: offset
            })
        });
        
        const data = response.specialties || [];
        
        // Filter by search if provided
        if (search) {
            const searchLower = search.toLowerCase();
            return data.filter(spec => 
                spec.title.toLowerCase().includes(searchLower) ||
                spec.spec_code.includes(search)
            );
        }
        
        return data;
    }
    
    async getSpecialty(code) {
        return this.request(`/specialties/${code}`);
    }
    
    // Schedule
    async getSchedule(groupId, date) {
        const params = new URLSearchParams();
        if (groupId) params.append('group', groupId);
        if (date) params.append('date', date);
        return this.request(`/schedule?${params}`);
    }
    
    async getGroups() {
        return this.request('/groups');
    }
    
    // News (if exists)
    async getNews(limit = 3) {
        return this.request(`/news?limit=${limit}`);
    }
}

export const api = new ApiClient(config.API_BASE);
