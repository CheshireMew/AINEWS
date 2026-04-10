import { useCallback, useEffect, useRef, useState } from 'react';

import { getPublicContent } from '../../api/content';

const PAGE_LIMIT = 20;
const MAX_PAGES = 50;

function createStreamState() {
    return {
        items: [],
        page: 0,
        hasMore: true,
        loading: false,
        loadingMore: false,
        loaded: false,
    };
}

function mergeUniqueById(previous, next) {
    const existingIds = new Set(previous.map((item) => item.id));
    return [...previous, ...next.filter((item) => !existingIds.has(item.id))];
}

export function usePublicStream(stream) {
    const [state, setState] = useState(createStreamState);
    const requestRef = useRef(0);
    const stateRef = useRef(state);

    useEffect(() => {
        stateRef.current = state;
    }, [state]);

    const fetchPage = useCallback(async (nextPage, { append = false, silent = false } = {}) => {
        const requestId = requestRef.current + 1;
        requestRef.current = requestId;

        if (!silent) {
            setState((previous) => ({
                ...previous,
                loading: append ? previous.loading : true,
                loadingMore: append,
            }));
        }

        try {
            const response = await getPublicContent(stream, PAGE_LIMIT, (nextPage - 1) * PAGE_LIMIT);
            if (requestRef.current !== requestId) {
                return;
            }
            const nextItems = response.data?.items || [];
            setState((previous) => ({
                ...previous,
                items: append ? mergeUniqueById(previous.items, nextItems) : nextItems,
                page: nextPage,
                hasMore: nextItems.length === PAGE_LIMIT && nextPage < MAX_PAGES,
                loading: false,
                loadingMore: false,
                loaded: true,
            }));
        } catch (error) {
            console.error(`Failed to fetch ${stream}:`, error);
            if (requestRef.current === requestId) {
                setState((previous) => ({
                    ...previous,
                    loading: false,
                    loadingMore: false,
                }));
            }
        }
    }, [stream]);

    const ensureLoaded = useCallback(async () => {
        const current = stateRef.current;
        if (current.loaded || current.loading) {
            return;
        }
        await fetchPage(1);
    }, [fetchPage]);

    const refresh = useCallback(async () => {
        const current = stateRef.current;
        if (!current.loaded || current.items.length === 0) {
            return;
        }

        try {
            const response = await getPublicContent(stream, PAGE_LIMIT, 0);
            const nextItems = response.data?.items || [];
            const knownIds = new Set(current.items.map((item) => item.id));
            const freshItems = nextItems.filter((item) => !knownIds.has(item.id));
            if (freshItems.length === 0) {
                return;
            }
            setState((previous) => ({
                ...previous,
                items: mergeUniqueById(freshItems, previous.items),
            }));
        } catch (error) {
            console.error(`Failed to refresh ${stream}:`, error);
        }
    }, [stream]);

    const loadMore = useCallback(async () => {
        const current = stateRef.current;
        if (!current.loaded || !current.hasMore || current.loadingMore || current.page >= MAX_PAGES) {
            return;
        }
        await fetchPage(current.page + 1, { append: true });
    }, [fetchPage]);

    return {
        state,
        ensureLoaded,
        refresh,
        loadMore,
    };
}
