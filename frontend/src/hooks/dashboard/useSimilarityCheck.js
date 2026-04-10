import { useState } from 'react';
import { message } from 'antd';

import { checkContentSimilarity } from '../../api/pipeline';
import { getRequestErrorMessage } from './listStateHelpers';

export function useSimilarityCheck() {
    const [newsId1, setNewsId1] = useState('');
    const [newsId2, setNewsId2] = useState('');
    const [similarityResult, setSimilarityResult] = useState(null);
    const [checkingLoading, setCheckingLoading] = useState(false);

    const checkSimilarity = async () => {
        if (!newsId1 || !newsId2) {
            message.warning('请输入两个新闻ID');
            return;
        }
        setCheckingLoading(true);
        try {
            const res = await checkContentSimilarity(parseInt(newsId1, 10), parseInt(newsId2, 10));
            setSimilarityResult(res.data);
            message.success('检测完成');
        } catch (error) {
            message.error(`检测失败: ${getRequestErrorMessage(error, '检测失败')}`);
            setSimilarityResult(null);
        } finally {
            setCheckingLoading(false);
        }
    };

    return {
        newsId1,
        newsId2,
        similarityResult,
        checkingLoading,
        setNewsId1,
        setNewsId2,
        checkSimilarity,
    };
}
