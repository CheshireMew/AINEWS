import { useCallback, useEffect, useRef, useState } from 'react';

import { getPublicReports } from '../../api/content';


function createReportState() {
    return {
        items: [],
        loading: false,
        loaded: false,
    };
}

export function usePublicReportFeed(kind) {
    const [state, setState] = useState(createReportState);
    const requestRef = useRef(0);
    const stateRef = useRef(state);

    useEffect(() => {
        stateRef.current = state;
    }, [state]);

    const ensureLoaded = useCallback(async () => {
        const current = stateRef.current;
        if (current.loaded || current.loading) {
            return;
        }

        const requestId = requestRef.current + 1;
        requestRef.current = requestId;
        setState((previous) => ({ ...previous, loading: true }));

        try {
            const response = await getPublicReports(kind, 10);
            if (requestRef.current !== requestId) {
                return;
            }
            setState({
                items: response.data?.items || [],
                loading: false,
                loaded: true,
            });
        } catch (error) {
            console.error(`Failed to fetch reports for ${kind}:`, error);
            if (requestRef.current === requestId) {
                setState((previous) => ({ ...previous, loading: false }));
            }
        }
    }, [kind]);

    return {
        state,
        ensureLoaded,
    };
}
