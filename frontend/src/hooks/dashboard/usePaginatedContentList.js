import { useCallback, useEffect, useRef, useState } from 'react';
import { message } from 'antd';

function defaultNormalizeResponse(payload, page, pageSize) {
    return {
        items: payload.data || [],
        pagination: {
            current: payload.page || page,
            pageSize: payload.limit || pageSize,
            total: payload.total || 0,
        },
        meta: null,
    };
}

export function usePaginatedContentList({
    contentKind,
    loadPage,
    active = true,
    initialPageSize = 10,
    enableSourceFilter = true,
    errorMessage = '加载内容失败',
    initialMeta = null,
    normalizeResponse = defaultNormalizeResponse,
}) {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(false);
    const [pagination, setPagination] = useState({ current: 1, pageSize: initialPageSize, total: 0 });
    const [meta, setMeta] = useState(initialMeta);
    const [filterSource, setFilterSource] = useState(undefined);
    const [filterKeyword, setFilterKeyword] = useState('');
    const fetchItemsRef = useRef(null);
    const previousActiveRef = useRef(active);
    const stateRef = useRef({
        pagination: { current: 1, pageSize: initialPageSize },
        filterSource: undefined,
        filterKeyword: '',
    });

    const fetchItems = useCallback(async (
        page = 1,
        pageSize = pagination.pageSize,
        source = filterSource,
        keyword = filterKeyword,
    ) => {
        setLoading(true);
        try {
            const res = await loadPage({
                page,
                limit: pageSize,
                source: enableSourceFilter ? source : undefined,
                keyword,
                kind: contentKind,
            });
            const payload = res.data || {};
            const normalized = normalizeResponse(payload, page, pageSize);
            setItems(normalized.items || []);
            setPagination(normalized.pagination || { current: page, pageSize, total: 0 });
            setMeta(normalized.meta ?? initialMeta);
        } catch (error) {
            console.error(errorMessage, error);
            message.error(errorMessage);
        } finally {
            setLoading(false);
        }
    }, [contentKind, enableSourceFilter, errorMessage, filterKeyword, filterSource, initialMeta, loadPage, normalizeResponse, pagination.pageSize]);

    fetchItemsRef.current = fetchItems;
    stateRef.current = { pagination, filterSource, filterKeyword };

    useEffect(() => {
        setFilterSource(undefined);
        setFilterKeyword('');
        setItems([]);
        setPagination({ current: 1, pageSize: initialPageSize, total: 0 });
        setMeta(initialMeta);
        previousActiveRef.current = active;
        if (!active) {
            return;
        }
        void fetchItemsRef.current?.(1, initialPageSize, undefined, '');
    }, [active, contentKind, initialMeta, initialPageSize]);

    useEffect(() => {
        const becameActive = active && !previousActiveRef.current;
        previousActiveRef.current = active;
        if (!becameActive) {
            return;
        }
        const current = stateRef.current;
        void fetchItemsRef.current?.(
            current.pagination.current,
            current.pagination.pageSize,
            current.filterSource,
            current.filterKeyword,
        );
    }, [active]);

    const refreshCurrent = useCallback(async () => {
        const current = stateRef.current;
        await fetchItemsRef.current?.(
            current.pagination.current,
            current.pagination.pageSize,
            current.filterSource,
            current.filterKeyword,
        );
    }, []);

    return {
        items,
        loading,
        pagination,
        meta,
        filterSource,
        filterKeyword,
        setFilterSource,
        setFilterKeyword,
        fetchItems,
        refreshCurrent,
    };
}
