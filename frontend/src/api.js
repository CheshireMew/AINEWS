import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000/api',
});

// Add a request interceptor to attach token if we have one
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
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
        if (error.response) {
            // Handle 401 Unauthorized
            if (error.response.status === 401) {
                // Clear token
                localStorage.removeItem('token');
                // Redirect to login if not already there
                if (!window.location.pathname.includes('/login')) {
                    window.location.href = '/login';
                }
            }

            if (error.response.data) {
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
        }

        // 默认错误处理
        throw error;
    }
);

export const login = async (username, password) => {
    const res = await api.post('/login', { username, password });
    // 响应拦截器已处理，res.data就是实际数据
    if (res.data.access_token) {
        localStorage.setItem('token', res.data.access_token);
    }
    return res.data;
};

export const getStats = (type = 'news') => api.get('/stats', { params: { type } });
export const getNews = (page = 1, limit = 50, source = null, stage = null, keyword = null, type = 'news') =>
    api.get('/news', { params: { page, limit, source, stage, keyword, type } });
export const getSpiders = () => api.get('/spiders');
export const getSpiderStatus = () => api.get('/spiders/status');
export const deleteNews = (id) => api.delete(`/news/${id}`);
export const runSpider = (name, items = 10) => api.post(`/spiders/run/${name}`, { items });
export const cancelScraper = (name) => api.post(`/spiders/stop/${name}`);
export const updateConfig = (name, { interval, limit }) => api.post(`/spiders/config/${name}`, { interval, limit });
export const deduplicateNews = (timeWindowHours, action = 'mark', threshold = 0.50, type = 'news') =>
    api.post('/news/deduplicate', { time_window_hours: timeWindowHours, action, threshold, type });
export const getDeduplicatedNews = (page = 1, limit = 50, source = null, keyword = null, type = 'news', stage = null) =>
    api.get('/deduplicated/news', { params: { page, limit, source, keyword, type, stage } });
export const getDeduplicatedStats = () =>
    api.get('/deduplicated/stats');

export const deleteDeduplicatedNews = (newsId) =>
    api.delete(`/deduplicated/news/${newsId}`);

export const batchRestoreDeduplicated = (type = 'news') =>
    api.post('/deduplicated/batch_restore_all', null, { params: { type } });

export const batchRestoreFiltered = (type = 'news') =>
    api.post('/filtered/batch_restore_all', null, { params: { type } });

export const getCuratedNews = (page = 1, limit = 50, source = null, keyword = null, type = 'news', ai_status = null) =>
    api.get('/curated/news', { params: { page, limit, source, keyword, type, ai_status } });

export const getCuratedStats = () => api.get('/curated/stats');

export const deleteCuratedNews = (newsId) =>
    api.delete(`/curated/news/${newsId}`);

export const restoreNews = (newsId, sourceTable = 'deduplicated_news') =>
    api.post(`/news/restore/${newsId}`, { source_table: sourceTable });

export const getFilteredDedupNews = (page = 1, limit = 50, keyword = null, type = 'news') =>
    api.get('/filtered/dedup/news', { params: { page, limit, keyword, type } });

// Blacklist APIs
export const getBlacklist = (type = 'news') => api.get('/blacklist', { params: { type } });
export const addBlacklist = (keyword, matchType = 'contains', type = 'news') => api.post('/blacklist', { keyword, match_type: matchType, type });
export const deleteBlacklist = (id) => api.delete(`/blacklist/${id}`);
export const filterNews = (timeRangeHours, type = 'news') => api.post('/news/filter', { time_range_hours: timeRangeHours, type });

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

export const getAiConfig = (type = 'news') => api.get('/ai/config', { params: { type } });
export const setAiConfig = (config, type = 'news') => api.post('/ai/config', config, { params: { type } });

// System API
export const updateCredentials = (data) => api.post('/system/credentials', data);
export const getSystemTimezone = () => api.get('/system/timezone');
export const setSystemTimezone = (config) => api.post('/system/timezone', config);
export const getDailyPushTime = () => api.get('/system/push_time');
export const setDailyPushTime = (data) => api.post('/system/push_time', data);

export const getFilteredCurated = (status, page = 1, limit = 50, source = null, keyword = null, type = 'news') =>
    api.get('/curated/filtered', { params: { status, page, limit, source, keyword, type } });

export const restoreCuratedNews = (id) => api.post(`/curated/restore/${id}`);
export const batchRestoreCurated = (type = 'news') => api.post('/curated/batch_restore', null, { params: { type } });
export const clearAllAiStatus = (type = 'news') => api.post('/curated/clear_all_ai_status', null, { params: { type } });

// Export News
export const getExportNews = (hours, minScore, type = 'news') => api.get('/curated/export', {
    params: { hours, min_score: minScore, type }
});



// Telegram APIs
export const getTelegramConfig = () => api.get('/telegram/config');
export const setTelegramConfig = (config) => api.post('/telegram/config', config);
export const testTelegramPush = () => api.post('/telegram/test');
export const sendNewsToTelegram = (newsIds) => api.post('/telegram/send_news', { news_ids: newsIds });
export const triggerDailyPush = () => api.post('/telegram/daily_push');

// Analyst API Keys
export const getAnalystApiKeys = () => api.get('/analyst/keys');
export const createAnalystApiKey = (keyName, notes) => api.post('/analyst/keys', { key_name: keyName, notes });
export const deleteAnalystApiKey = (keyId) => api.delete(`/analyst/keys/${keyId}`);

export const getDeepSeekConfig = () => api.get('/deepseek/config');
export const setDeepSeekConfig = (config) => api.post('/deepseek/config', config);
export const testDeepSeekConnection = () => api.post('/deepseek/test');

// Auto-Pipeline Config APIs
export const getAutoPipelineConfig = () => api.get('/config/auto_pipeline');
export const setAutoPipelineConfig = (config) => api.post('/config/auto_pipeline', config);

// Check Similarity API
export const checkNewsSimilarity = (newsId1, newsId2) =>
    api.post('/news/check_similarity', { news_id_1: newsId1, news_id_2: newsId2 });

export default api;
