import React, { useState } from 'react';
import { Card, Button, Input, Select, Table, Tag, Space, message, Popconfirm } from 'antd';
import { filterCuratedNews, getFilteredCurated, deleteCuratedNews, batchRestoreCurated } from '../../api';

const { Option } = Select;
const { TextArea } = Input;

/**
 * AI筛选Tab组件
 * 用于执行AI筛选并管理rejected的新闻
 */
const AIFilterTab = () => {
    // AI筛选配置状态
    const [aiFilterPrompt, setAiFilterPrompt] = useState('');
    const [aiFilterHours, setAiFilterHours] = useState(8);
    const [aiFiltering, setAiFiltering] = useState(false);

    // Rejected新闻状态
    const [rejectedNews, setRejectedNews] = useState([]);
    const [rejectedLoading, setRejectedLoading] = useState(false);
    const [rejectedPagination, setRejectedPagination] = useState({ current: 1, pageSize: 20, total: 0 });

    /**
     * 加载rejected新闻
     */
    const fetchRejectedNews = async (page = 1) => {
        setRejectedLoading(true);
        try {
            const res = await getFilteredCurated('rejected', page, rejectedPagination.pageSize);
            setRejectedNews(res.data.data);
            setRejectedPagination({
                ...rejectedPagination,
                current: page,
                total: res.data.total
            });
        } catch (e) {
            message.error('加载失败: ' + (e.response?.data?.detail || e.message));
        } finally {
            setRejectedLoading(false);
        }
    };

    /**
     * 执行AI筛选
     */
    const handleAIFilter = async () => {
        if (!aiFilterPrompt.trim()) {
            message.warning('请输入筛选提示词');
            return;
        }

        setAiFiltering(true);
        try {
            const res = await filterCuratedNews(aiFilterPrompt, aiFilterHours);
            message.success(`AI筛选完成！批准: ${res.data.approved_count}, 拒绝: ${res.data.rejected_count}`);
            fetchRejectedNews(1); // 刷新rejected列表
        } catch (e) {
            message.error('AI筛选失败: ' + (e.response?.data?.detail || e.message));
        } finally {
            setAiFiltering(false);
        }
    };

    /**
     * 删除rejected新闻
     */
    const handleDeleteRejected = async (id) => {
        try {
            await deleteCuratedNews(id);
            message.success('删除成功（已从所有表中永久删除）');
            fetchRejectedNews(rejectedPagination.current);
        } catch (e) {
            message.error('删除失败: ' + (e.response?.data?.detail || e.message));
        }
    };

    /**
     * 批量恢复
     */
    const handleBatchRestore = async () => {
        try {
            const res = await batchRestoreCurated();
            message.success(`批量恢复成功！恢复了 ${res.data.restored_count} 条新闻`);
            fetchRejectedNews(1);
        } catch (e) {
            message.error('恢复失败: ' + (e.response?.data?.detail || e.message));
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
        },
        {
            title: '操作',
            width: 100,
            render: (_, record) => (
                <Popconfirm
                    title="确定删除这条新闻？"
                    description="此操作将从所有表中永久删除"
                    onConfirm={() => handleDeleteRejected(record.id)}
                >
                    <Button type="link" danger size="small">删除</Button>
                </Popconfirm>
            )
        }
    ];

    return (
        <div style={{ padding: '0 10px' }}>
            {/* AI筛选配置 */}
            <Card title="AI筛选配置" style={{ marginBottom: 16 }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                        <div style={{ marginBottom: 8 }}>筛选提示词:</div>
                        <TextArea
                            rows={4}
                            value={aiFilterPrompt}
                            onChange={(e) => setAiFilterPrompt(e.target.value)}
                            placeholder="输入AI筛选提示词..."
                        />
                    </div>
                    <Space>
                        <span>时间范围:</span>
                        <Select value={aiFilterHours} style={{ width: 120 }} onChange={setAiFilterHours}>
                            <Option value={6}>6小时内</Option>
                            <Option value={8}>8小时内</Option>
                            <Option value={12}>12小时内</Option>
                            <Option value={24}>24小时内</Option>
                        </Select>
                        <Button type="primary" onClick={handleAIFilter} loading={aiFiltering}>
                            开始AI筛选
                        </Button>
                    </Space>
                </Space>
            </Card>

            {/* Rejected新闻列表 */}
            <Card
                title="已拒绝的新闻"
                extra={
                    <Button onClick={handleBatchRestore}>
                        批量恢复所有rejected
                    </Button>
                }
            >
                <Button
                    onClick={() => fetchRejectedNews(1)}
                    style={{ marginBottom: 16 }}
                    loading={rejectedLoading}
                >
                    刷新列表
                </Button>

                <Table
                    dataSource={rejectedNews}
                    columns={columns}
                    rowKey="id"
                    loading={rejectedLoading}
                    pagination={{
                        ...rejectedPagination,
                        onChange: fetchRejectedNews
                    }}
                />
            </Card>
        </div>
    );
};

export default AIFilterTab;
