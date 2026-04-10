import { listReviewQueue } from '../../api/content';
import { usePaginatedContentList } from './usePaginatedContentList';

export function useReviewQueueTab(contentKind, active) {
    return usePaginatedContentList({
        contentKind,
        loadPage: listReviewQueue,
        active,
        errorMessage: '加载待审核内容失败',
    });
}
