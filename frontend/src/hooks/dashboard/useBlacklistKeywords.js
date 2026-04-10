import { useCallback, useEffect, useState } from 'react';
import { message } from 'antd';

import { addBlocklist, deleteBlocklist, getBlocklist } from '../../api/config';

export function useBlacklistKeywords(contentKind, active) {
    const [blacklistKeywords, setBlacklistKeywords] = useState([]);
    const [newKeyword, setNewKeyword] = useState('');
    const [newMatchType, setNewMatchType] = useState('contains');

    const fetchBlacklistData = useCallback(async () => {
        try {
            const res = await getBlocklist(contentKind);
            setBlacklistKeywords(res.data.keywords || []);
        } catch (error) {
            console.error('Fetch blocklist failed', error);
        }
    }, [contentKind]);

    const addKeyword = async () => {
        if (!newKeyword.trim()) {
            return;
        }
        try {
            await addBlocklist(newKeyword.trim(), newMatchType, contentKind);
            message.success('添加成功');
            setNewKeyword('');
            await fetchBlacklistData();
        } catch {
            message.error('添加失败');
        }
    };

    const removeKeyword = async (id) => {
        try {
            await deleteBlocklist(id);
            message.success('删除成功');
            await fetchBlacklistData();
        } catch {
            message.error('删除失败');
        }
    };

    useEffect(() => {
        if (!active) {
            return;
        }
        const timerId = window.setTimeout(() => {
            void fetchBlacklistData();
        }, 0);
        return () => window.clearTimeout(timerId);
    }, [active, fetchBlacklistData]);

    return {
        blacklistKeywords,
        newKeyword,
        newMatchType,
        setNewKeyword,
        setNewMatchType,
        addKeyword,
        removeKeyword,
    };
}
