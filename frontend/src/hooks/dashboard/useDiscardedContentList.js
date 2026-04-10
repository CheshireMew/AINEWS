import { listReviewedContent } from '../../api/content';
import { REVIEW_DECISION } from '../../contracts/content';
import { usePaginatedContentList } from './usePaginatedContentList';

export function useDiscardedContentList(contentKind) {
    return usePaginatedContentList({
        contentKind,
        loadPage: (params) => listReviewedContent({ decision: REVIEW_DECISION.DISCARDED, ...params }),
        initialPageSize: 10,
        enableSourceFilter: false,
        errorMessage: '加载已舍弃内容失败',
    });
}
