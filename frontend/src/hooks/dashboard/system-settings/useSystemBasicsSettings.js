import { useEffect, useState } from 'react';
import { message } from 'antd';

import {
    getAutomationConfig,
    getDeliverySchedule,
    getSystemTimezone,
    setAutomationConfig,
    setDeliverySchedule as setDeliveryScheduleConfig,
    setSystemTimezone,
} from '../../../api/config';
import { getRequestErrorMessage } from '../listStateHelpers';

export function useSystemBasicsSettings() {
    const [timezone, setTimezone] = useState('Asia/Shanghai');
    const [loading, setLoading] = useState(false);
    const [newsConfig, setNewsConfig] = useState({
        dedup_hours: 2,
        dedup_window_hours: 2,
        filter_hours: 24,
        ai_scoring_hours: 10,
        push_hours: 12,
    });
    const [articleConfig, setArticleConfig] = useState({
        dedup_hours: 168,
        dedup_window_hours: 72,
        filter_hours: 168,
        ai_scoring_hours: 168,
        push_hours: 72,
    });
    const [deliverySchedule, setDeliverySchedule] = useState({
        news_time: '20:00',
        article_time: '21:00',
    });

    useEffect(() => {
        void Promise.all([loadTimezone(), loadAutomationConfig(), loadDeliverySchedule()]);
    }, []);

    const loadTimezone = async () => {
        try {
            const res = await getSystemTimezone();
            if (res.data?.timezone) {
                setTimezone(res.data.timezone);
            }
        } catch (error) {
            console.error('Failed to fetch timezone', error);
        }
    };

    const loadAutomationConfig = async () => {
        try {
            const res = await getAutomationConfig();
            if (res.data?.news) {
                setNewsConfig((prev) => ({ ...prev, ...res.data.news }));
            }
            if (res.data?.article) {
                setArticleConfig((prev) => ({ ...prev, ...res.data.article }));
            }
        } catch (error) {
            console.error('Failed to fetch automation config', error);
        }
    };

    const loadDeliverySchedule = async () => {
        try {
            const res = await getDeliverySchedule();
            setDeliverySchedule((prev) => ({
                news_time: res.data?.news_time || prev.news_time,
                article_time: res.data?.article_time || prev.article_time,
            }));
        } catch (error) {
            console.error('Failed to fetch delivery schedule', error);
        }
    };

    const updateHours = (scope, key, value) => {
        const setter = scope === 'news' ? setNewsConfig : setArticleConfig;
        setter((prev) => ({ ...prev, [key]: value }));
    };

    const save = async () => {
        setLoading(true);
        try {
            await setSystemTimezone({ timezone });
            await setAutomationConfig({ news: newsConfig, article: articleConfig });
            await setDeliveryScheduleConfig(deliverySchedule);
            message.success('系统配置已更新');
        } catch (error) {
            message.error(`保存失败: ${getRequestErrorMessage(error, '保存失败')}`);
        } finally {
            setLoading(false);
        }
    };

    return {
        timezone,
        loading,
        newsConfig,
        articleConfig,
        deliverySchedule,
        setTimezone,
        setDeliverySchedule,
        updateHours,
        save,
    };
}
