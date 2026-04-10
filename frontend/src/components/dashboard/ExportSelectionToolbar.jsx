import React from 'react';
import PropTypes from 'prop-types';
import { Card, Button, Space, Tag } from 'antd';
import { SendOutlined } from '@ant-design/icons';

export default function ExportSelectionToolbar({
    visibleCount,
    selectedCount,
    sendingToTg,
    clearSelection,
    toggleSelectAll,
    invertSelection,
    copyPlainText,
    copyMarkdown,
    copyTelegramHtml,
    sendToTelegram,
}) {
    if (visibleCount === 0) {
        return null;
    }

    return (
        <Card style={{ marginBottom: 16 }}>
            <div style={{ marginBottom: 12 }}>
                <Tag color="blue">已选 {selectedCount}/{visibleCount} 条</Tag>
            </div>
            <Space wrap>
                <Button onClick={toggleSelectAll}>
                    {selectedCount === visibleCount ? '取消全选' : '全选'}
                </Button>
                <Button onClick={invertSelection}>反选</Button>
                <Button onClick={clearSelection}>清空</Button>
                <div style={{ borderLeft: '1px solid #d9d9d9', height: 32, margin: '0 8px' }} />
                <Button type="primary" onClick={copyPlainText}>复制为纯文本</Button>
                <Button onClick={copyMarkdown}>Markdown格式</Button>
                <Button onClick={copyTelegramHtml}>TG格式</Button>
                <Button icon={<SendOutlined />} onClick={sendToTelegram} loading={sendingToTg}>
                    发送到TG
                </Button>
            </Space>
        </Card>
    );
}

ExportSelectionToolbar.propTypes = {
    visibleCount: PropTypes.number.isRequired,
    selectedCount: PropTypes.number.isRequired,
    sendingToTg: PropTypes.bool.isRequired,
    clearSelection: PropTypes.func.isRequired,
    toggleSelectAll: PropTypes.func.isRequired,
    invertSelection: PropTypes.func.isRequired,
    copyPlainText: PropTypes.func.isRequired,
    copyMarkdown: PropTypes.func.isRequired,
    copyTelegramHtml: PropTypes.func.isRequired,
    sendToTelegram: PropTypes.func.isRequired,
};
