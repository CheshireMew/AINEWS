import { useCallback, useEffect, useRef, useState } from 'react';

import { getContentOverview, getContentStats } from '../../api/content';
import { DEFAULT_DASHBOARD_OVERVIEW } from '../../contracts/content';


export function useDashboardOverviewData(contentKind) {
    const [stats, setStats] = useState([]);
    const [overview, setOverview] = useState(DEFAULT_DASHBOARD_OVERVIEW);
    const requestRef = useRef(0);

    const refreshOverview = useCallback(async ({ includeStats = false } = {}) => {
        const requestId = requestRef.current + 1;
        requestRef.current = requestId;
        try {
            if (includeStats) {
                const [statsRes, overviewRes] = await Promise.all([
                    getContentStats(contentKind),
                    getContentOverview(contentKind),
                ]);
                if (requestRef.current !== requestId) {
                    return;
                }
                setStats(statsRes.data.stats || []);
                setOverview({ ...DEFAULT_DASHBOARD_OVERVIEW, ...(overviewRes.data || {}) });
                return;
            }

            const overviewRes = await getContentOverview(contentKind);
            if (requestRef.current !== requestId) {
                return;
            }
            setOverview({ ...DEFAULT_DASHBOARD_OVERVIEW, ...(overviewRes.data || {}) });
        } catch (error) {
            console.error('Failed to fetch dashboard overview:', error);
        }
    }, [contentKind]);

    useEffect(() => {
        const timer = setTimeout(() => {
            void refreshOverview({ includeStats: true });
        }, 0);
        return () => clearTimeout(timer);
    }, [refreshOverview]);

    return {
        stats,
        overview,
        refreshOverview,
    };
}
