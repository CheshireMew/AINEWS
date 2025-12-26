import React from 'react';

/**
 * 新闻详情展开组件
 * 用于在表格行展开时显示新闻的详细内容和元数据
 */
const NewsExpandedView = ({ record }) => {
    if (!record) return null;

    return (
        <div style={{ padding: 16, background: '#fafafa' }}>
            <p><strong>URL:</strong> <a href={record.source_url} target="_blank" rel="noopener noreferrer">{record.source_url}</a></p>
            {/* 可以添加更多元数据，如 site_importance_flag 等 */}
            {record.site_importance_flag && (
                <p><strong>Flag:</strong> {record.site_importance_flag}</p>
            )}
            <div style={{ whiteSpace: 'pre-wrap', maxHeight: 400, overflowY: 'auto', marginTop: 8 }}>
                {record.content || <span style={{ color: '#ccc' }}>No content available</span>}
            </div>
        </div>
    );
};

export default NewsExpandedView;
