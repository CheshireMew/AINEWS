import { useState } from 'react';
import { message } from 'antd';

import { runReview } from '../../api/pipeline';
import { getRequestErrorMessage, refreshListPage } from './listStateHelpers';

export function useReviewRunner(contentKind, reviewPrompt, reviewHours, listState, saveSettings) {
    const [running, setRunning] = useState(false);
    const [logs, setLogs] = useState([]);

    const addLog = (text) => {
        setLogs((previous) => [...previous, `${new Date().toLocaleTimeString()} ${text}`]);
    };

    const runReviewFlow = async () => {
        if (!reviewPrompt.trim()) {
            message.warning('请输入审核提示词');
            return;
        }
        const saved = await saveSettings();
        if (!saved) {
            return;
        }
        setRunning(true);
        setLogs([]);
        try {
            while (true) {
                const res = await runReview({ filter_prompt: reviewPrompt, hours: reviewHours, kind: contentKind });
                const { processed, discarded, selected, total } = res.data;
                addLog(`本轮处理 ${processed} 条，舍弃 ${discarded} 条，选入 ${selected} 条，待处理总量 ${total}`);
                if (processed === 0 || processed >= total) {
                    break;
                }
            }
            message.success('审核完成');
            await refreshListPage(listState, { page: 1, source: undefined });
        } catch (error) {
            message.error(`审核失败: ${getRequestErrorMessage(error, '审核失败')}`);
        } finally {
            setRunning(false);
        }
    };

    return {
        running,
        logs,
        runReviewFlow,
    };
}
