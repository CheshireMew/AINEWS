import { useEffect, useState } from 'react';

import { searchPublicContent } from '../../api/content';
import { CONTENT_KIND } from '../../contracts/content';


export function usePublicSearchResults(query) {
    const [state, setState] = useState({
        loading: false,
        articleItems: [],
        briefItems: [],
    });
    const normalizedQuery = query.trim();
    const enabled = normalizedQuery.length >= 2;

    useEffect(() => {
        if (!enabled) {
            return;
        }

        let cancelled = false;

        const timer = setTimeout(() => {
            const load = async () => {
                setState((previous) => ({ ...previous, loading: true }));
                try {
                    const [articleResponse, briefResponse] = await Promise.all([
                        searchPublicContent(normalizedQuery, CONTENT_KIND.ARTICLE, 50, 0),
                        searchPublicContent(normalizedQuery, CONTENT_KIND.NEWS, 50, 0),
                    ]);
                    if (cancelled) {
                        return;
                    }
                    setState({
                        loading: false,
                        articleItems: articleResponse.data?.items || [],
                        briefItems: briefResponse.data?.items || [],
                    });
                } catch (error) {
                    if (cancelled) {
                        return;
                    }
                    console.error('Failed to search public content:', error);
                    setState({
                        loading: false,
                        articleItems: [],
                        briefItems: [],
                    });
                }
            };

            void load();
        }, 0);

        return () => {
            cancelled = true;
            clearTimeout(timer);
        };
    }, [enabled, normalizedQuery]);

    return {
        state,
        enabled,
    };
}
