import client from './client';
import { CONTENT_KIND } from '../contracts/content';

export const getSpiders = () => client.get('/spiders');
export const getSpiderStatus = () => client.get('/spiders/status');
export const runSpider = (name, items = 10) => client.post(`/spiders/run/${name}`, { items });
export const cancelScraper = (name) => client.post(`/spiders/stop/${name}`);
export const updateConfig = (name, { interval, limit }) => client.post(`/spiders/config/${name}`, { interval, limit });

export const buildArchive = ({ time_window_hours, action = 'mark', threshold = 0.5, kind = CONTENT_KIND.NEWS }) =>
    client.post('/content/archive/build', { time_window_hours, action, threshold, kind });

export const checkContentSimilarity = (newsId1, newsId2) =>
    client.post('/content/archive/check_similarity', { news_id_1: newsId1, news_id_2: newsId2 });

export const runReview = (params) => client.post('/content/review/run', params);
export const applyBlocklist = (timeRangeHours, kind = CONTENT_KIND.NEWS) => client.post('/content/blocked/apply', { time_range_hours: timeRangeHours, kind });
export const restoreBlockedContent = (kind = CONTENT_KIND.NEWS) => client.post('/content/blocked/restore', null, { params: { kind } });
export const requeueReviewEntry = (id) => client.post(`/content/review/${id}/requeue`);
export const requeueReviewedContent = (kind = CONTENT_KIND.NEWS) => client.post('/content/review/requeue', null, { params: { kind } });
export const clearReviewDecisions = (kind = CONTENT_KIND.NEWS) => client.post('/content/review/clear', null, { params: { kind } });

export const testTelegramPush = () => client.post('/delivery/test');
export const sendSelectedContent = (newsIds) => client.post('/delivery/send', { news_ids: newsIds });
export const triggerDailyPush = (kind = CONTENT_KIND.NEWS) => client.post(`/delivery/daily/${kind}`);

export const getAnalystApiKeys = () => client.get('/integration/analyst/keys');
export const createAnalystApiKey = (keyName, notes) => client.post('/integration/analyst/keys', { key_name: keyName, notes });
export const deleteAnalystApiKey = (keyId) => client.delete(`/integration/analyst/keys/${keyId}`);
export const testDeepSeekConnection = () => client.post('/integration/ai/test');
