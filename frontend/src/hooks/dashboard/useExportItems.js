import { useState } from 'react';
import dayjs from 'dayjs';
import { message } from 'antd';

import { listReviewedContent } from '../../api/content';
import { REVIEW_DECISION } from '../../contracts/content';
import { getRequestErrorMessage } from './listStateHelpers';

export function useExportItems(contentKind, manuallyFeatured, setManuallyFeatured) {
    const [exportTimeRange, setExportTimeRange] = useState(24);
    const [exportMinScore, setExportMinScore] = useState(6);
    const [selectedPool, setSelectedPool] = useState([]);
    const [loading, setLoading] = useState(false);

    const visibleItems = [
        ...manuallyFeatured.map((item) => ({ ...item, isFeatured: true })),
        ...selectedPool.filter((item) => !manuallyFeatured.some((manual) => manual.id === item.id)),
    ];

    const loadItems = async () => {
        try {
            setLoading(true);
            setManuallyFeatured([]);
            const res = await listReviewedContent({
                decision: REVIEW_DECISION.SELECTED,
                page: 1,
                limit: 500,
                kind: contentKind,
            });
            const cutoff = dayjs().subtract(exportTimeRange, 'hour');
            const nextItems = (res.data.data || []).filter((item) => {
                const score = item.review_score ?? 0;
                return score >= exportMinScore && dayjs(item.published_at).isAfter(cutoff);
            });
            setSelectedPool(nextItems);
            message.success(`加载了 ${nextItems.length} 条内容`);
        } catch (error) {
            message.error(`加载失败: ${getRequestErrorMessage(error, '加载失败')}`);
        } finally {
            setLoading(false);
        }
    };

    return {
        exportTimeRange,
        exportMinScore,
        visibleItems,
        loading,
        setExportTimeRange,
        setExportMinScore,
        loadItems,
    };
}
