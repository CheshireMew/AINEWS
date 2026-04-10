import { useCallback, useEffect, useRef, useState } from 'react';
import { message } from 'antd';

import { createRssSource, deleteRssSource, getRssSources, updateRssSource } from '../../api/config';
import { cancelScraper, getSpiderStatus, getSpiders, runSpider, updateConfig } from '../../api/pipeline';
import { getRequestErrorMessage } from './listStateHelpers';

const RUNTIME_REFRESH_INTERVAL_MS = 3000;

function mergeSpiderStatus(previous, nextStatus) {
    const merged = { ...previous };
    for (const [spider, status] of Object.entries(nextStatus)) {
        const previousSpider = previous[spider] || {};
        merged[spider] = {
            ...previousSpider,
            ...status,
            logs: status.logs && status.logs.length > 0 ? status.logs : previousSpider.logs || [],
        };
    }
    return merged;
}

export function useDashboardScraperRuntimeData() {
    const [spiders, setSpiders] = useState([]);
    const [spiderStatus, setSpiderStatus] = useState({});
    const [rssSources, setRssSources] = useState([]);
    const requestRef = useRef(0);

    const refreshRuntime = useCallback(async ({ includeCatalog = false } = {}) => {
        const requestId = requestRef.current + 1;
        requestRef.current = requestId;
        try {
            const requests = [getSpiderStatus()];
            if (includeCatalog) {
                requests.unshift(getSpiders(), getRssSources());
            }

            const responses = await Promise.all(requests);
            if (requestRef.current !== requestId) {
                return;
            }

            const statusResponse = responses[responses.length - 1];
            setSpiderStatus((previous) => mergeSpiderStatus(previous, statusResponse.data || {}));

            if (includeCatalog) {
                const [spidersResponse, rssSourcesResponse] = responses;
                setSpiders(spidersResponse.data.spiders || []);
                setRssSources(rssSourcesResponse.data.sources || []);
            }
        } catch (error) {
            console.error('Failed to fetch scraper runtime:', error);
        }
    }, []);

    useEffect(() => {
        const timer = setTimeout(() => {
            void refreshRuntime({ includeCatalog: true });
        }, 0);

        const interval = setInterval(() => {
            void refreshRuntime();
        }, RUNTIME_REFRESH_INTERVAL_MS);

        return () => {
            clearTimeout(timer);
            clearInterval(interval);
        };
    }, [refreshRuntime]);

    const handleRunSpider = useCallback(async (name, items) => {
        try {
            await runSpider(name, items);
            message.success(`已触发爬虫: ${name} (Max ${items})`);
            await refreshRuntime();
        } catch (error) {
            console.error('Run scraper failed:', error);
            message.error(`触发失败: ${getRequestErrorMessage(error, name)}`);
        }
    }, [refreshRuntime]);

    const handleStopSpider = useCallback(async (name) => {
        try {
            await cancelScraper(name);
            message.warning(`已请求停止爬虫: ${name}`);
            await refreshRuntime();
        } catch (error) {
            message.error(`停止失败: ${getRequestErrorMessage(error, name)}`);
        }
    }, [refreshRuntime]);

    const handleConfigChange = useCallback(async (name, changes) => {
        try {
            await updateConfig(name, changes);
            message.success(`已更新配置: ${name}`);
            await refreshRuntime();
        } catch (error) {
            message.error(`更新配置失败: ${getRequestErrorMessage(error, '更新配置失败')}`);
        }
    }, [refreshRuntime]);

    const handleCreateRssSource = useCallback(async (payload) => {
        try {
            await createRssSource(payload);
            message.success('RSS 源已创建');
            await refreshRuntime({ includeCatalog: true });
        } catch (error) {
            message.error(`创建失败: ${getRequestErrorMessage(error, '创建 RSS 源失败')}`);
            throw error;
        }
    }, [refreshRuntime]);

    const handleUpdateRssSource = useCallback(async (id, payload) => {
        try {
            await updateRssSource(id, payload);
            message.success('RSS 源已更新');
            await refreshRuntime({ includeCatalog: true });
        } catch (error) {
            message.error(`更新失败: ${getRequestErrorMessage(error, '更新 RSS 源失败')}`);
            throw error;
        }
    }, [refreshRuntime]);

    const handleDeleteRssSource = useCallback(async (id) => {
        try {
            await deleteRssSource(id);
            message.success('RSS 源已删除');
            await refreshRuntime({ includeCatalog: true });
        } catch (error) {
            message.error(`删除失败: ${getRequestErrorMessage(error, '删除 RSS 源失败')}`);
            throw error;
        }
    }, [refreshRuntime]);

    return {
        spiders,
        spiderStatus,
        rssSources,
        refreshRuntime,
        actions: {
            handleRunSpider,
            handleStopSpider,
            handleConfigChange,
            handleCreateRssSource,
            handleUpdateRssSource,
            handleDeleteRssSource,
        },
    };
}
