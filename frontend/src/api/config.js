import client from './client';
import { CONTENT_KIND } from '../contracts/content';

export const getSystemTimezone = () => client.get('/system/timezone');
export const setSystemTimezone = (config) => client.post('/system/timezone', config);

export const getDeliverySchedule = () => client.get('/delivery/schedule');
export const setDeliverySchedule = (data) => client.post('/delivery/schedule', data);

export const getAutomationConfig = () => client.get('/config/automation');
export const setAutomationConfig = (config) => client.post('/config/automation', config);

export const getAiProviderConfig = () => client.get('/integration/ai');
export const setAiProviderConfig = (config) => client.post('/integration/ai', config);

export const getReviewSettings = (kind = CONTENT_KIND.NEWS) => client.get('/review/settings', { params: { kind } });
export const setReviewSettings = (config, kind = CONTENT_KIND.NEWS) => client.post('/review/settings', config, { params: { kind } });

export const getBlocklist = (kind = CONTENT_KIND.NEWS) => client.get('/content/blocklist', { params: { kind } });
export const addBlocklist = (keyword, matchType = 'contains', kind = CONTENT_KIND.NEWS) => client.post('/content/blocklist', { keyword, match_type: matchType, kind });
export const deleteBlocklist = (id) => client.delete(`/content/blocklist/${id}`);

export const getTelegramConfig = () => client.get('/integration/telegram');
export const setTelegramConfig = (config) => client.post('/integration/telegram', config);

export const getRssSources = () => client.get('/rss/sources');
export const createRssSource = (config) => client.post('/rss/sources', config);
export const updateRssSource = (id, config) => client.put(`/rss/sources/${id}`, config);
export const deleteRssSource = (id) => client.delete(`/rss/sources/${id}`);
