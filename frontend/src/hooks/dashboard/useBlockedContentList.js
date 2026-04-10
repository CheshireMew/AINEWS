import { listBlockedContent } from '../../api/content';
import { usePaginatedContentList } from './usePaginatedContentList';

export function useBlockedContentList(contentKind, active) {
    return usePaginatedContentList({
        contentKind,
        loadPage: listBlockedContent,
        active,
        initialPageSize: 10,
        enableSourceFilter: false,
        errorMessage: '加载已拦截内容失败',
    });
}
