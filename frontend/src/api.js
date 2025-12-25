import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000/api',
});

// Add a request interceptor to attach token if we have one
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        // config.headers.Authorization = `Bearer ${token}`; 
    }
    return config;
});

export const login = async (password) => {
    const res = await api.post('/login', { password });
    if (res.data.token) {
        localStorage.setItem('token', res.data.token);
    }
    return res.data;
};

export const getStats = () => api.get('/stats');
export const getNews = (page = 1, limit = 50, source = null, stage = null) =>
    api.get('/news', { params: { page, limit, source, stage } });
export const getSpiders = () => api.get('/spiders');
export const getSpiderStatus = () => api.get('/spiders/status');
export const deleteNews = (id) => api.delete(`/news/${id}`);
export const runSpider = (name, items = 10) => api.post(`/spiders/run/${name}`, { items });
export const cancelScraper = (name) => api.post(`/spiders/stop/${name}`);
export const updateConfig = (name, { interval, limit }) => api.post(`/spiders/config/${name}`, { interval, limit });
export const deduplicateNews = (timeWindowHours, action = 'mark') =>
    api.post('/news/deduplicate', { time_window_hours: timeWindowHours, action });
export const getDeduplicatedNews = (page = 1, limit = 50, source = null) =>
    api.get('/deduplicated/news', { params: { page, limit, source } });
export const getDeduplicatedStats = () =>
    api.get('/deduplicated/stats');

export const deleteDeduplicatedNews = (newsId) =>
    api.delete(`/deduplicated/news/${newsId}`);

export const getCuratedNews = (page = 1, limit = 50, source = null) =>
    api.get('/curated/news', { params: { page, limit, source } });

export const getCuratedStats = () => api.get('/curated/stats');

export const deleteCuratedNews = (newsId) =>
    api.delete(`/curated/news/${newsId}`);

export const restoreNews = (newsId, sourceTable = 'deduplicated_news') =>
    api.post(`/news/restore/${newsId}`, { source_table: sourceTable });

export const getFilteredDedupNews = (page = 1, limit = 50) =>
    api.get('/filtered/dedup/news', { params: { page, limit } });

// Blacklist APIs
export const getBlacklist = () => api.get('/blacklist');
export const addBlacklist = (keyword, matchType = 'contains') => api.post('/blacklist', { keyword, match_type: matchType });
export const deleteBlacklist = (id) => api.delete(`/blacklist/${id}`);
export const filterNews = (timeRangeHours) => api.post('/news/filter', { time_range_hours: timeRangeHours });

// Export API
export const exportNews = (params) => {
    // Return the URL for direct download or use Blob
    // For large files, direct window.open or link click with params is easier, 
    // but we might need token auth if enabled.
    // Since simple auth is token in localStorage, we should use fetch/axios with blob.
    return api.get('/export', {
        params,
        responseType: 'blob'
    });
};


export default api;
