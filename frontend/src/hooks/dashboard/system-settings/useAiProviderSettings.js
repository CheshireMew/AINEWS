import { useEffect, useState } from 'react';
import { message } from 'antd';

import { getAiProviderConfig, setAiProviderConfig } from '../../../api/config';
import { testDeepSeekConnection } from '../../../api/pipeline';
import { getRequestErrorMessage } from '../listStateHelpers';

const MODEL_BASE_URLS = {
    'deepseek-chat': 'https://api.deepseek.com',
    'deepseek-reasoner': 'https://api.deepseek.com',
    'gpt-4o': 'https://api.openai.com/v1',
    'gpt-4o-mini': 'https://api.openai.com/v1',
    'claude-3-5-sonnet-20240620': 'https://api.anthropic.com/v1',
};

export function useAiProviderSettings() {
    const [config, setConfig] = useState({ api_key: '', base_url: 'https://api.deepseek.com', model: 'deepseek-chat' });

    async function loadConfig() {
        try {
            const res = await getAiProviderConfig();
            setConfig(res.data);
        } catch (error) {
            console.error('Failed to fetch AI provider config', error);
        }
    }

    useEffect(() => {
        const timer = setTimeout(() => {
            void loadConfig();
        }, 0);
        return () => clearTimeout(timer);
    }, []);

    const save = async () => {
        try {
            await setAiProviderConfig(config);
            message.success('AI 配置已保存');
        } catch (error) {
            message.error(`保存失败: ${getRequestErrorMessage(error, '保存失败')}`);
        }
    };

    const test = async () => {
        try {
            await testDeepSeekConnection();
            message.success('连接测试成功');
        } catch (error) {
            message.error(`连接测试失败: ${getRequestErrorMessage(error, '连接测试失败')}`);
        }
    };

    const handleModelChange = (model) => {
        setConfig((prev) => ({ ...prev, model, base_url: MODEL_BASE_URLS[model] || prev.base_url }));
    };

    return { config, setConfig, save, test, handleModelChange };
}
