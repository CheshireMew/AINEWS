import client from './client';
import { CONTENT_KIND } from '../contracts/content';

export const getContentOverview = (kind = CONTENT_KIND.NEWS) => client.get('/content/overview', { params: { kind } });
export const getContentStats = (kind = CONTENT_KIND.NEWS) => client.get('/content/stats', { params: { kind } });

export const listIncomingContent = ({ page = 1, limit = 50, source = null, keyword = null, kind = CONTENT_KIND.NEWS } = {}) =>
    client.get('/content/incoming', { params: { page, limit, source, keyword, kind } });
export const deleteIncomingContent = (id) => client.delete(`/content/incoming/${id}`);
export const deleteSourceContent = (id) => client.delete(`/content/source/${id}`);

export const listSourceGroups = ({ page = 1, limit = 20, source = null, keyword = null, kind = CONTENT_KIND.NEWS } = {}) =>
    client.get('/content/source/groups', { params: { page, limit, source, keyword, kind } });

export const listArchiveContent = ({ page = 1, limit = 50, source = null, keyword = null, kind = CONTENT_KIND.NEWS } = {}) =>
    client.get('/content/archive', { params: { page, limit, source, keyword, kind } });
export const deleteArchiveContent = (id) => client.delete(`/content/archive/${id}`);

export const listBlockedContent = ({ page = 1, limit = 50, keyword = null, kind = CONTENT_KIND.NEWS } = {}) =>
    client.get('/content/blocked', { params: { page, limit, keyword, kind } });

export const listReviewQueue = ({ page = 1, limit = 50, source = null, keyword = null, kind = CONTENT_KIND.NEWS } = {}) =>
    client.get('/content/review', { params: { page, limit, source, keyword, kind } });

export const listReviewedContent = ({ decision, page = 1, limit = 50, source = null, keyword = null, kind = CONTENT_KIND.NEWS } = {}) =>
    client.get('/content/decisions', { params: { decision, page, limit, source, keyword, kind } });

export const deleteReviewEntry = (id) => client.delete(`/content/review/${id}`);
export const restoreArchiveEntry = (id) => client.post(`/content/archive/${id}/restore`);
export const restoreBlockedEntry = (id) => client.post(`/content/blocked/${id}/restore`);

export const exportContent = (params) => client.get('/content/export', { params, responseType: 'blob' });

export const getPublicContent = (stream, limit = 20, offset = 0) =>
    client.get('/public/content', { params: { stream, limit, offset } });

export const getPublicReports = (kind = null, limit = 20, offset = 0) =>
    client.get('/public/reports', { params: { kind, limit, offset } });

export const searchPublicContent = (query, kind = 'all', limit = 20, offset = 0) =>
    client.get('/public/search', { params: { query, kind, limit, offset } });
