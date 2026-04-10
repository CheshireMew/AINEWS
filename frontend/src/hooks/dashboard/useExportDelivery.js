import { useState } from 'react';
import { message } from 'antd';

import { sendSelectedContent, triggerDailyPush } from '../../api/pipeline';
import { getRequestErrorMessage } from './listStateHelpers';

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

export function useExportDelivery(contentKind, visibleItems, selectedIds) {
    const [sendingToTg, setSendingToTg] = useState(false);

    const getSelectedItems = () => visibleItems.filter((item) => selectedIds.includes(item.id));

    const copyPlainText = () => {
        const selected = getSelectedItems();
        if (selected.length === 0) {
            message.warning('请先选择要复制的内容');
            return;
        }
        const text = selected
            .map((item) => `${item.title}\n\n${item.content || item.review_summary || ''}`.trim())
            .join('\n\n---\n\n');
        navigator.clipboard.writeText(text);
        message.success(`已复制 ${selected.length} 条内容`);
    };

    const copyMarkdown = () => {
        const selected = getSelectedItems();
        if (selected.length === 0) {
            message.warning('请先选择要复制的内容');
            return;
        }
        const text = selected
            .map((item) => {
                const content = (item.content || item.review_summary || 'No Content').replace(/\n/g, '\n>\n> ');
                return `### [${item.title}](${item.source_url})\n\n> ${content}\n\n---`;
            })
            .join('\n\n');
        navigator.clipboard.writeText(text);
        message.success(`已复制 ${selected.length} 条内容`);
    };

    const copyTelegramHtml = async () => {
        const selected = getSelectedItems();
        if (selected.length === 0) {
            message.warning('请先选择要复制的内容');
            return;
        }
        const htmlContent = selected
            .map((item) => `⚡ <b><a href="${item.source_url}">${escapeHtml(item.title)}</a></b>`)
            .join('<br><br>\n');
        const plainText = selected.map((item) => `${item.title}\n${item.source_url}`).join('\n\n');
        try {
            const htmlBlob = new Blob([htmlContent], { type: 'text/html' });
            const textBlob = new Blob([plainText], { type: 'text/plain' });
            await navigator.clipboard.write([
                new ClipboardItem({
                    'text/html': htmlBlob,
                    'text/plain': textBlob,
                }),
            ]);
            message.success(`已复制 ${selected.length} 条内容`);
        } catch (error) {
            console.error('Copy failed:', error);
            message.error('复制失败，请重试');
        }
    };

    const sendToTelegram = async () => {
        const selected = getSelectedItems();
        if (selected.length === 0) {
            message.warning('请先选择要发送的内容');
            return;
        }
        try {
            setSendingToTg(true);
            const res = await sendSelectedContent(selectedIds);
            message.success(`成功发送 ${res.data.sent_count || selected.length} 条内容到 Telegram`);
        } catch (error) {
            message.error(getRequestErrorMessage(error, '发送失败，请检查 Telegram 配置'));
        } finally {
            setSendingToTg(false);
        }
    };

    const triggerDailyDelivery = async () => {
        try {
            message.loading('正在触发日报推送...', 1);
            const res = await triggerDailyPush(contentKind);
            if (res.data?.status === 'success') {
                message.success(`推送成功: 已发送 ${res.data.count} 条内容`);
            } else if (res.data?.status === 'skipped') {
                message.warning(`推送跳过: ${res.data.message}`);
            } else {
                message.warning('推送完成，请检查 Telegram');
            }
        } catch (error) {
            message.error(`触发失败: ${getRequestErrorMessage(error, '触发失败')}`);
        }
    };

    return {
        sendingToTg,
        copyPlainText,
        copyMarkdown,
        copyTelegramHtml,
        sendToTelegram,
        triggerDailyDelivery,
    };
}
