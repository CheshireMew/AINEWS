import React, { useState } from 'react';
import { Card, Table, Tag, Space, message } from 'antd';
import { getFilteredCurated } from '../../api';

/**
 * AI精选Tab组件
 * 显示AI批准的新闻
 */
const AIBestTab = () => {
    const [approvedNews, setApprovedNews] = useState([]);
    const [approvedLoading, setApprovedLoading] = useState(false);
    const [approvedPagination, setApprovedPagination] = useState({ current: 1, pageSize: 20, total: 0 });

    /**
     * 加载approved新闻
     */
    const fetchApprovedNews = async (page = 1) => {
        setApprovedLoading(true);
        try {
            const res = await getFilteredCurated('approved', page, approvedPagination.pageSize);
            setApprovedNews(res.data.data);
            setApprovedPagination({
                ...approvedPagination,
                current: page,
                total: res.data.total
            });
        } catch (e) {
            message.error('加载失败: ' + (e.response?.data?.detail || e.message));
        } finally {
            setApprovedLoading(false);
        }
    };

    // 表格列定义
    const columns = [
        {
            title: '标题',
            dataIndex: 'title',
            render: (text, record) => <a href={record.source_url} target="_blank" rel="noopener noreferrer">{text}</a>
        },
        {
            title: '来源',
            dataIndex: 'source_site',
            width: 100,
            render: (text) => <Tag>{text}</Tag>
        },
        {
            title: 'AI评价',
            dataIndex: 'ai_summary',
            width: 300,
            ellipsis: true
        }
    ];

    // 组件加载时获取数据
    React.useEffect(() => {
        fetchApprovedNews(1);
    }, []);

    return (
        <div style={{ padding: '0 10px' }}>
            <Card title="AI批准的新闻">
                <Table
                    dataSource={approvedNews}
                    columns={columns}
                    rowKey="id"
                    loading={approvedLoading}
                    pagination={{
                        ...approvedPagination,
                        onChange: fetchApprovedNews
                    }}
                />
            </Card>
        </div>
    );
};

export default AIBestTab;
