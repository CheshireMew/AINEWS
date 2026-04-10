import { useCallback, useEffect, useState } from 'react';
import { message } from 'antd';

import { getReviewSettings, setReviewSettings } from '../../api/config';

export function useReviewSettings(contentKind) {
    const [reviewPrompt, setReviewPrompt] = useState('');
    const [reviewHours, setReviewHours] = useState(8);

    const fetchSettings = useCallback(async () => {
        try {
            const res = await getReviewSettings(contentKind);
            if (res.data?.prompt !== undefined) {
                setReviewPrompt(res.data.prompt);
            }
            if (res.data?.hours) {
                setReviewHours(res.data.hours);
            }
        } catch (error) {
            console.error('加载审核配置失败', error);
        }
    }, [contentKind]);

    const saveSettings = async () => {
        try {
            await setReviewSettings({ prompt: reviewPrompt, hours: reviewHours }, contentKind);
            message.success('配置已保存');
            return true;
        } catch {
            message.error('保存配置失败');
            return false;
        }
    };

    useEffect(() => {
        const timerId = window.setTimeout(() => {
            void fetchSettings();
        }, 0);
        return () => window.clearTimeout(timerId);
    }, [fetchSettings]);

    return {
        reviewPrompt,
        reviewHours,
        setReviewPrompt,
        setReviewHours,
        saveSettings,
    };
}
