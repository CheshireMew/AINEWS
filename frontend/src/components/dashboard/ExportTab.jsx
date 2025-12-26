import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { Card, Select, Button, Space, message, DatePicker } from 'antd';
import { getExportNews } from '../../api';

const { Option } = Select;

/**
 * 新闻输出Tab组件
 * 用于加载、筛选和导出AI评分的新闻
 */
const ExportTab = ({ manuallyFeatured, setManuallyFeatured }) => {
    // 筛选条件状态
    const [exportTimeRange, setExportTimeRange] = useState(24); // 24小时
    const [exportMinScore, setExportMinScore] = useState(6); // 最低6分

    // 数据状态
    const [exportNews, setExportNews] = useState([]);
    const [newsExportLoading, setNewsExportLoading] = useState(false);
    const [selectedNewsIds, setSelectedNewsIds] = useState([]);

    /**
     * 加载新闻
     */
    const handleLoadNews = async () => {
        try {
            setNewsExportLoading(true);
            // 清空手动加精列表
            setManuallyFeatured([]);
            const res = await getExportNews(exportTimeRange, exportMinScore);
            setExportNews(res.data.news || []);
            setSelectedNewsIds([]);
            message.success(`加载了 ${res.data.news?.length || 0} 条新闻`);
        } catch (e) {
            message.error('加载失败: ' + (e.response?.data?.detail || e.message));
        } finally {
            setNewsExportLoading(false);
        }
    };

    /**
     * 复制为纯文本
     */
    const handleCopyPlainText = () => {
        const selected = exportNews.filter(n => selectedNewsIds.includes(n.id));
        if (selected.length === 0) {
            message.warning('请先选择要复制的新闻');
            return;
        }
        const text = selected.map(n => {
            if (n.content) {
                return `${n.title}\n\n${n.content}`;
            }
            return n.title;
        }).join('\n\n---\n\n');
        navigator.clipboard.writeText(text);
        message.success(`已复制 ${selected.length} 条新闻（含标题和内容）`);
    };

    /**
     * 复制为Markdown格式
     */
    const handleCopyMarkdown = () => {
        const selected = exportNews.filter(n => selectedNewsIds.includes(n.id));
        if (selected.length === 0) {
            message.warning('请先选择要复制的新闻');
            return;
        }
        const text = selected.map(n => `- [${n.title}](${n.source_url})`).join('\n');
        navigator.clipboard.writeText(text);
        message.success(`已复制 ${selected.length} 条新闻（Markdown）`);
    };

    /**
     * 复制为TG格式
     */
    const handleCopyTG = () => {
        const selected = exportNews.filter(n => selectedNewsIds.includes(n.id));
        if (selected.length === 0) {
            message.warning('请先选择要复制的新闻');
            return;
        }
        const text = selected.map(n => `<a href="${n.source_url}">${n.title}</a>`).join('\n');
        navigator.clipboard.writeText(text);
        message.success(`已复制 ${selected.length} 条新闻（TG格式）`);
    };

    /**
     * 全选/取消全选
     */
    const handleToggleSelectAll = () => {
        if (selectedNewsIds.length === exportNews.length) {
            setSelectedNewsIds([]);
        } else {
            setSelectedNewsIds(exportNews.map(n => n.id));
        }
    };

    /**
     * 反选
     */
    const handleInvertSelection = () => {
        const allIds = exportNews.map(n => n.id);
        const newSelected = allIds.filter(id => !selectedNewsIds.includes(id));
        setSelectedNewsIds(newSelected);
    };

    // 表格列定义
    const columns = [
        {
            title: '评分',
            dataIndex: 'score',
            width: 120,
            render: (score, record) => (
                <Space>
                    {record.isFeatured && <Tag color="gold">⭐手动</Tag>}
                    {score && <Tag color={score >= 8 ? 'green' : score >= 7 ? 'blue' : 'default'}>{score}分</Tag>}
                </Space>
            )
        },
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
            title: 'AI标签',
            dataIndex: 'ai_explanation',
            width: 200,
            ellipsis: true,
            render: (text) => {
                if (!text) return '-';
                const parts = text.split(' - ');
                if (parts.length < 2) return text;
                const reason = parts[1]?.split('#')[0]?.trim() || '';
                return <span style={{ fontSize: 12, color: '#666' }}>{reason}</span>;
            }
        }
    ];

    return (
        <div style={{ padding: '0 10px' }}>
            {/* 筛选条件 */}
            <Card style={{ marginBottom: 16 }}>
                <Space size="large">
                    <div>
                        <span style={{ marginRight: 8 }}>时间范围:</span>
                        <Select value={exportTimeRange} style={{ width: 120 }} onChange={setExportTimeRange}>
                            <Option value={6}>6小时内</Option>
                            <Option value={12}>12小时内</Option>
                            <Option value={24}>24小时内</Option>
                            <Option value={48}>48小时内</Option>
                        </Select>
                    </div>
                    <div>
                        <span style={{ marginRight: 8 }}>最低评分:</span>
                        <Select value={exportMinScore} style={{ width: 100 }} onChange={setExportMinScore}>
                            <Option value={4}>≥ 4分</Option>
                            <Option value={5}>≥ 5分</Option>
                            <Option value={6}>≥ 6分</Option>
                            <Option value={7}>≥ 7分</Option>
                            <Option value={8}>≥ 8分</Option>
                            <Option value={9}>≥ 9分</Option>
                        </Select>
                    </div>
                    <Button
                        type="primary"
                        onClick={handleLoadNews}
                        loading={newsExportLoading}
                    >
                        加载新闻
                    </Button>
                </Space>
            </Card>

            {/* 操作按钮 */}
            {exportNews.length > 0 && (
                <Card style={{ marginBottom: 16 }}>
                    <div style={{ marginBottom: 12 }}>
                        <Tag color="blue">已选 {selectedNewsIds.length}/{exportNews.length} 条</Tag>
                    </div>
                    <Space wrap>
                        <Button onClick={handleToggleSelectAll}>
                            {selectedNewsIds.length === exportNews.length ? '取消全选' : '全选'}
                        </Button>
                        <Button onClick={handleInvertSelection}>反选</Button>
                        <Button onClick={() => setSelectedNewsIds([])}>清空</Button>
                        <div style={{ borderLeft: '1px solid #d9d9d9', height: 32, margin: '0 8px' }} />
                        <Button type="primary" onClick={handleCopyPlainText}>复制为纯文本</Button>
                        <Button onClick={handleCopyMarkdown}>Markdown格式</Button>
                        <Button onClick={handleCopyTG}>TG格式</Button>
                    </Space>
                </Card>
            )}

            {/* 新闻列表 */}
            <Table
                dataSource={[
                    ...manuallyFeatured.map(n => ({ ...n, isFeatured: true })),
                    ...exportNews
                ]}
                rowKey="id"
                loading={newsExportLoading}
                pagination={false}
                rowSelection={{
                    selectedRowKeys: selectedNewsIds,
                    onChange: (selectedKeys) => setSelectedNewsIds(selectedKeys)
                }}
                expandable={{
                    expandedRowRender: (record) => (
                        <div style={{ padding: '12px 24px', backgroundColor: '#fafafa' }}>
                            <p style={{ margin: 0, whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
                                {record.content || '暂无内容'}
                            </p>
                        </div>
                    ),
                    rowExpandable: (record) => !!record.content
                }}
                columns={columns}
            />
        </div>
    );
};

ExportTab.propTypes = {
    manuallyFeatured: PropTypes.arrayOf(PropTypes.object)
};

export default ExportTab;
