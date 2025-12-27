import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Card, Button, Input, Select, Table, Tag, Space, message, Popconfirm } from 'antd';
import {
    filterCuratedNews, getFilteredCurated, deleteCuratedNews, batchRestoreCurated, getAiConfig, setAiConfig, restoreCuratedNews, clearAllAiStatus,
    restoreNews
} from '../../api';
import NewsExpandedView from './NewsExpandedView';
import NewsToolbar from './NewsToolbar';
import TimeRangeSelect from './TimeRangeSelect';

const { Option } = Select;
const { TextArea } = Input;

/**
 * AI筛选Tab组件
 * 用于执行AI筛选并管理rejected的新闻
 */
const AIFilterTab = ({ onAddToFeatured }) => {
    // AI筛选配置状态
    const [aiFilterPrompt, setAiFilterPrompt] = useState('');
    const [aiFilterHours, setAiFilterHours] = useState(8);
    const [aiFiltering, setAiFiltering] = useState(false);

    // Explicitly define logs state
    const [logs, setLogs] = useState([]);

    // Helper to add log
    const addLog = (msg) => {
        setLogs(prev => [...prev, `${new Date().toLocaleTimeString()} ${msg}`]);
    };

    // Rejected新闻状态
    const [rejectedNews, setRejectedNews] = useState([]);
    const [rejectedLoading, setRejectedLoading] = useState(false);
    const [rejectedPagination, setRejectedPagination] = useState({ current: 1, pageSize: 10, total: 0 });
    const [filterKeyword, setFilterKeyword] = useState('');

    // 加载AI配置
    useEffect(() => {
        const fetchAiConfig = async () => {
            try {
                const res = await getAiConfig();
                if (res.data) {
                    if (res.data.prompt) setAiFilterPrompt(res.data.prompt);
                    if (res.data.hours) setAiFilterHours(res.data.hours);
                }
            } catch (e) {
                console.error("Failed to fetch AI config", e);
            }
        };
        fetchAiConfig();

        // 初始加载rejected列表
        fetchRejectedNews(1);
    }, []);

    // 保存AI配置
    const handleSaveAiConfig = async () => {
        try {
            await setAiConfig({ prompt: aiFilterPrompt, hours: aiFilterHours });
        } catch (e) {
            console.error("Failed to save AI config", e);
        }
    };

    /**
     * 加载rejected新闻
     */
    const fetchRejectedNews = async (page = 1, keyword = filterKeyword) => {
        setRejectedLoading(true);
        try {
            const res = await getFilteredCurated('rejected', page, 10, null, keyword);
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

        // 先保存配置
        await handleSaveAiConfig();

        setAiFiltering(true);
        setLogs([]); // Reset logs
        let totalProcessed = 0;
        let totalFiltered = 0;
        let batchCount = 0;

        try {
            while (true) {
                batchCount++;
                addLog(`⏳ Batch ${batchCount}: Requesting AI analysis...`);
                const res = await filterCuratedNews({ filter_prompt: aiFilterPrompt, hours: aiFilterHours });
                const { processed, filtered, total, results } = res.data;

                // Log detailed results from backend
                // Accumulate stats first to show correct progress
                totalProcessed += processed;
                totalFiltered += filtered;

                // Calculate original total estimate:
                // Backend returns 'total' as current pending count.
                // So (total returned by backend) + (processed count before this batch) = Original Total.
                const processedBeforeThisBatch = totalProcessed - processed;
                const estimatedTotal = total + processedBeforeThisBatch;

                // Show concise progress log
                const percent = estimatedTotal > 0 ? Math.round((totalProcessed / estimatedTotal) * 100) : 100;
                addLog(`✅ Batch ${batchCount}: Analyzed ${processed} items (${filtered} rejected). Progress: ${totalProcessed}/${estimatedTotal} (${percent}%)`);

                // Stop logging detailed individual items as per user request
                /* 
                if (results && results.length > 0) { ... } 
                */



                // Loop termination condition:
                // If we processed everything available (or nothing was available)
                if (processed === 0 || processed >= total) {
                    break;
                }

                // Small delay to be safe
                await new Promise(r => setTimeout(r, 500));
            }

            message.success(`AI筛选全量完成！共处理: ${totalProcessed}, 拒绝: ${totalFiltered}`);
            fetchRejectedNews(1); // 刷新rejected列表
        } catch (e) {
            message.error('AI筛选失败: ' + (e.response?.data?.detail || e.message));
        } finally {
            setAiFiltering(false);
        }
    };

    /**
     * 还原单条新闻
     */
    const handleRestoreCurated = async (id) => {
        try {
            await restoreCuratedNews(id);
            message.success('已还原');
            fetchRejectedNews(rejectedPagination.current);
        } catch (e) {
            message.error('还原失败: ' + (e.response?.data?.detail || e.message));
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
     * 批量恢复所有rejected
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

    /**
     * 清除所有AI状态
     */
    const handleClearAllAiStatus = async () => {
        try {
            const res = await clearAllAiStatus();
            message.success(`已清除所有AI状态！共清除 ${res.data.cleared_count} 条`);
            fetchRejectedNews(1);
        } catch (e) {
            message.error('清除失败: ' + (e.response?.data?.detail || e.message));
        }
    };

    // 表格列定义
    const columns = [
        { title: 'ID', dataIndex: 'id', width: 60 },
        {
            title: '标题',
            dataIndex: 'title',
            render: (text, record) => <a href={record.source_url} target="_blank" rel="noopener noreferrer">{text}</a>
        },
        {
            title: 'AI 标签',
            dataIndex: 'ai_explanation',
            width: 200,
            render: (text) => {
                if (!text) return <span style={{ color: '#ccc' }}>-</span>;

                // 解析格式: "8分-技术创新 #AI技术"
                const parts = text.split(' ');
                const scoreAndReason = parts[0]; // "8分-技术创新"
                const tag = parts[1]; // "#AI技术"

                const [score, reason] = scoreAndReason.split('-');

                return (
                    <span>
                        <Tag color="blue">{score}</Tag>
                        {reason && <span style={{ color: '#666', marginRight: 4 }}>{reason}</span>}
                        {tag && <Tag color="green">{tag}</Tag>}
                    </span>
                );
            }
        },
        { title: '来源', dataIndex: 'source_site', width: 100 },
        {
            title: '发布时间',
            dataIndex: 'published_at',
            width: 160,
            render: text => new Date(text).toLocaleString()
        },
        {
            title: '操作',
            width: 200,
            render: (_, record) => (
                <Space>
                    <Button
                        type="primary"
                        size="small"
                        onClick={() => onAddToFeatured && onAddToFeatured(record)}
                    >
                        加精
                    </Button>
                    <Button type="link" onClick={() => handleRestoreCurated(record.id)}>还原</Button>
                    <Popconfirm
                        title="确定删除这条新闻？"
                        description="此操作将从所有表中永久删除"
                        onConfirm={() => handleDeleteRejected(record.id)}
                    >
                        <Button type="link" danger>删除</Button>
                    </Popconfirm>
                </Space>
            )
        }
    ];

    return (
        <div style={{ padding: '0 10px' }}>
            {/* AI筛选配置 */}
            <Card title="AI筛选配置" style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', gap: 24 }}>
                    {/* 左侧：配置区域 (宽度 50%) */}
                    <div style={{ flex: 1 }}>
                        <Space vertical style={{ width: '100%' }}>
                            <div>
                                <div style={{ marginBottom: 8 }}>筛选提示词:</div>
                                <TextArea
                                    rows={6}
                                    value={aiFilterPrompt}
                                    onChange={(e) => setAiFilterPrompt(e.target.value)}
                                    placeholder="输入AI筛选提示词..."
                                />
                            </div>
                            <Space>
                                <span>时间范围:</span>
                                <TimeRangeSelect value={aiFilterHours} onChange={setAiFilterHours} />
                                <Button type="primary" onClick={handleAIFilter} loading={aiFiltering}>
                                    开始AI筛选
                                </Button>
                            </Space>
                        </Space>
                    </div>

                    {/* 右侧：Console Output (宽度 50%) */}
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                        <div style={{ marginBottom: 8 }}>运行日志:</div>
                        <div style={{
                            background: '#000',
                            color: '#0f0',
                            padding: '12px',
                            borderRadius: 4,
                            fontSize: 12,
                            height: '240px', // Fixed height matching left side approx
                            overflowY: 'auto',
                            fontFamily: 'monospace',
                            width: '100%' // Ensure full width of container
                        }}>
                            <div style={{ color: '#8c8c8c', marginBottom: 8, borderBottom: '1px solid #333', paddingBottom: 4 }}>
                                &gt; CONSOLE OUTPUT
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                {logs.length === 0 && !aiFiltering ? (
                                    <div style={{ color: '#666' }}>&gt; Ready to run.</div>
                                ) : (
                                    logs.map((log, index) => (
                                        <div key={index} style={{ wordBreak: 'break-all' }}>&gt; {log}</div>
                                    ))
                                )}
                                {aiFiltering && <div style={{ color: '#aaa', fontStyle: 'italic' }}>... Processing ...</div>}
                            </div>
                        </div>
                    </div>
                </div>
            </Card>

            {/* Rejected新闻列表 */}
            <Card
                title="已拒绝的新闻"
            >
                <NewsToolbar
                    onSearch={(val) => {
                        setFilterKeyword(val);
                        fetchRejectedNews(1, val);
                    }}
                    onRefresh={() => fetchRejectedNews(rejectedPagination.current, filterKeyword)}
                    loading={rejectedLoading}
                >
                    <Popconfirm
                        title="确定恢复所有?"
                        description="将把所有已拒绝的新闻恢复为初始状态"
                        onConfirm={handleBatchRestore}
                    >
                        <Button>
                            批量恢复所有rejected
                        </Button>
                    </Popconfirm>
                    <Popconfirm
                        title="确定清除所有AI状态？"
                        description="将把所有已筛选的新闻恢复为未筛选状态"
                        onConfirm={handleClearAllAiStatus}
                    >
                        <Button danger>
                            清除所有AI状态
                        </Button>
                    </Popconfirm>
                </NewsToolbar>

                <Table
                    dataSource={rejectedNews}
                    columns={columns}
                    rowKey="id"
                    loading={rejectedLoading}
                    pagination={{
                        ...rejectedPagination,
                        onChange: (page) => fetchRejectedNews(page, filterKeyword)
                    }}
                    expandable={{
                        expandedRowRender: record => <NewsExpandedView record={record} />,
                        rowExpandable: record => true,
                    }}
                />
            </Card>
        </div>
    );
};

AIFilterTab.propTypes = {
    onAddToFeatured: PropTypes.func
};

export default AIFilterTab;
