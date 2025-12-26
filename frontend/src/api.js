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

// Add a response interceptor to handle the new API format
api.interceptors.response.use(
    (response) => {
        // 新的API格式: { success: true, data: {...}, message: "...", pagination: {...} }
        // 为了向后兼容，我们需要处理新旧两种格式

        const data = response.data;

        // 检查是否是新格式（有success字段）
        if (data && typeof data.success !== 'undefined') {
            // 新格式：提取data，并保留pagination等其他字段
            // 将response.data替换为实际数据，但保留其他元数据
            if (data.pagination) {
                // 分页响应：将data和pagination都保留
                return {
                    ...response,
                    data: {
                        data: data.data,
                        total: data.pagination.total,
                        page: data.pagination.page,
                        limit: data.pagination.limit,
                        pages: data.pagination.pages
                    }
                };
            } else {
                // 普通响应：直接返回data
                return {
                    ...response,
                    data: data.data || data
                };
            }
        }

        // 旧格式：直接返回
        return response;
    },
    (error) => {
        // 处理错误响应
        if (error.response && error.response.data) {
            const errorData = error.response.data;

            // 新格式的错误: { success: false, message: "...", error: {...} }
            if (errorData.success === false) {
                // 使用自定义消息
                const customError = new Error(errorData.message || '请求失败');
                customError.response = error.response;
                customError.errorType = errorData.error?.type;
                customError.errorDetails = errorData.error?.details;
                throw customError;
            }
        }

        // 默认错误处理
        throw error;
    }
);

export const login = async (password) => {
    const res = await api.post('/login', { password });
    // 响应拦截器已处理，res.data就是实际数据
    if (res.data.token) {
        localStorage.setItem('token', res.data.token);
    }
    return res.data;
};

export const getStats = () => api.get('/stats');
export const getNews = (page = 1, limit = 50, source = null, stage = null, keyword = null) =>
    api.get('/news', { params: { page, limit, source, stage, keyword } });
export const getSpiders = () => api.get('/spiders');
export const getSpiderStatus = () => api.get('/spiders/status');
export const deleteNews = (id) => api.delete(`/news/${id}`);
export const runSpider = (name, items = 10) => api.post(`/spiders/run/${name}`, { items });
export const cancelScraper = (name) => api.post(`/spiders/stop/${name}`);
export const updateConfig = (name, { interval, limit }) => api.post(`/spiders/config/${name}`, { interval, limit });
export const deduplicateNews = (timeWindowHours, action = 'mark') =>
    api.post('/news/deduplicate', { time_window_hours: timeWindowHours, action });
export const getDeduplicatedNews = (page = 1, limit = 50, source = null, keyword = null) =>
    api.get('/deduplicated/news', { params: { page, limit, source, keyword } });
export const getDeduplicatedStats = () =>
    api.get('/deduplicated/stats');

export const deleteDeduplicatedNews = (newsId) =>
    api.delete(`/deduplicated/news/${newsId}`);

export const batchRestoreDeduplicated = () =>
    api.post('/deduplicated/batch_restore_all');

export const batchRestoreFiltered = () =>
    api.post('/filtered/batch_restore_all');

export const getCuratedNews = (page = 1, limit = 50, source = null, keyword = null) =>
    api.get('/curated/news', { params: { page, limit, source, keyword } });

export const getCuratedStats = () => api.get('/curated/stats');

export const deleteCuratedNews = (newsId) =>
    api.delete(`/curated/news/${newsId}`);

export const restoreNews = (newsId, sourceTable = 'deduplicated_news') =>
    api.post(`/news/restore/${newsId}`, { source_table: sourceTable });

export const getFilteredDedupNews = (page = 1, limit = 50, keyword = null) =>
    api.get('/filtered/dedup/news', { params: { page, limit, keyword } });

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

// AI Filtering APIs
export const filterCuratedNews = (params) =>
    api.post('/curated/ai_filter', params);

export const getAiConfig = () => api.get('/ai/config');
export const setAiConfig = (config) => api.post('/ai/config', config);

export const getFilteredCurated = (status, page = 1, limit = 50, source = null, keyword = null) =>
    api.get('/curated/filtered', { params: { status, page, limit, source, keyword } });

export const restoreCuratedNews = (id) => api.post(`/curated/restore/${id}`);
export const batchRestoreCurated = () => api.post('/curated/batch_restore');
export const clearAllAiStatus = () => api.post('/curated/clear_all_ai_status');

// Export News
export const getExportNews = (hours, minScore) => api.get('/curated/export', {
    params: { hours, min_score: minScore }
});



// Telegram APIs
export const getTelegramConfig = () => api.get('/telegram/config');
export const setTelegramConfig = (config) => api.post('/telegram/config', config);
export const testTelegramPush = () => api.post('/telegram/test');

export const getDeepSeekConfig = () => api.get('/deepseek/config');
export const setDeepSeekConfig = (config) => api.post('/deepseek/config', config);
export const testDeepSeekConnection = () => api.post('/deepseek/test');

export default api;
