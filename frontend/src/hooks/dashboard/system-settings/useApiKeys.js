import { useEffect, useState } from 'react';
import { message } from 'antd';

import { createAnalystApiKey, deleteAnalystApiKey, getAnalystApiKeys } from '../../../api/pipeline';
import { getRequestErrorMessage } from '../listStateHelpers';

export function useApiKeys() {
    const [apiKeys, setApiKeys] = useState([]);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [newKeyName, setNewKeyName] = useState('');
    const [newKeyNotes, setNewKeyNotes] = useState('');

    async function loadApiKeys() {
        try {
            const res = await getAnalystApiKeys();
            setApiKeys(res.data || []);
        } catch (error) {
            console.error('Failed to fetch analyst API keys', error);
        }
    }

    useEffect(() => {
        const timer = setTimeout(() => {
            void loadApiKeys();
        }, 0);
        return () => clearTimeout(timer);
    }, []);

    const resetModal = () => {
        setShowCreateModal(false);
        setNewKeyName('');
        setNewKeyNotes('');
    };

    const createKey = async () => {
        if (!newKeyName.trim()) {
            message.warning('请输入密钥名称');
            return;
        }
        try {
            const res = await createAnalystApiKey(newKeyName, newKeyNotes);
            message.success(`密钥创建成功: ${res.data.key_name}`);
            resetModal();
            await loadApiKeys();
        } catch (error) {
            message.error(`创建失败: ${getRequestErrorMessage(error, '创建失败')}`);
        }
    };

    const deleteKey = async (keyId, keyName) => {
        try {
            await deleteAnalystApiKey(keyId);
            message.success(`密钥 "${keyName}" 已删除`);
            await loadApiKeys();
        } catch (error) {
            message.error(`删除失败: ${getRequestErrorMessage(error, '删除失败')}`);
        }
    };

    const copyKey = (apiKey) => {
        navigator.clipboard.writeText(apiKey);
        message.success('密钥已复制到剪贴板');
    };

    return {
        apiKeys,
        showCreateModal,
        newKeyName,
        newKeyNotes,
        setShowCreateModal,
        setNewKeyName,
        setNewKeyNotes,
        resetModal,
        createKey,
        deleteKey,
        copyKey,
    };
}
