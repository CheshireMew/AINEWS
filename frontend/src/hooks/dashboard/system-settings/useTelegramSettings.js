import { useEffect, useState } from 'react';
import { message } from 'antd';

import { getTelegramConfig, setTelegramConfig } from '../../../api/config';
import { testTelegramPush } from '../../../api/pipeline';
import { getRequestErrorMessage } from '../listStateHelpers';

export function useTelegramSettings() {
    const [config, setConfig] = useState({ bot_token: '', chat_id: '', enabled: false });

    async function loadConfig() {
        try {
            const res = await getTelegramConfig();
            setConfig(res.data);
        } catch (error) {
            console.error('Failed to fetch Telegram config', error);
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
            await setTelegramConfig(config);
            message.success('Telegram 配置已保存');
        } catch (error) {
            message.error(`保存失败: ${getRequestErrorMessage(error, '保存失败')}`);
        }
    };

    const test = async () => {
        try {
            await testTelegramPush();
            message.success('测试消息发送成功，请检查 Telegram');
        } catch (error) {
            message.error(`测试发送失败: ${getRequestErrorMessage(error, '测试发送失败')}`);
        }
    };

    return { config, setConfig, save, test };
}
