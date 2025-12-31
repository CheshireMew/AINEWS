import React, { useState, useEffect } from 'react';
import usePaginationConfig from '../common/usePaginationConfig';
import PropTypes from 'prop-types';
import { Table, Button, Select, Space, message, Popconfirm, InputNumber } from 'antd';
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import { getDeduplicatedNews, restoreNews, deduplicateNews, deleteDeduplicatedNews, batchRestoreDeduplicated } from '../../api';
import NewsExpandedView from './NewsExpandedView';
import NewsToolbar from './NewsToolbar';
import TimeRangeSelect from './TimeRangeSelect';
import BatchRestoreButton from './BatchRestoreButton';

const { Option } = Select;

/**
 * 去重数据Tab组件
 * 用于管理已去重的新闻数据
 */
const DeduplicatedTab = ({ spiders, onAddToFeatured, onShowExport, contentType }) => {
    const { getPaginationConfig } = usePaginationConfig();
    // 状态管理
    const [dedupNews, setDedupNews] = useState([]);
    const [loadingDedup, setLoadingDedup] = useState(false);
    const [dedupPagination, setDedupPagination] = useState({ current: 1, pageSize: 10, total: 0 });
    const [dedupFilterSource, setDedupFilterSource] = useState(undefined);
    const [filterKeyword, setFilterKeyword] = useState('');

    // Deduplication controls
    const [dedupTimeRange, setDedupTimeRange] = useState(8);
    // Load from localStorage or default to 0.50
    const [threshold, setThreshold] = useState(() => {
        try {
            const saved = localStorage.getItem('dedup_threshold');
            if (saved !== null) {
                const parsed = parseFloat(saved);
                if (!isNaN(parsed)) {
                    return parsed;
                }
            }
        } catch (e) {
            console.warn('Failed to load threshold from localStorage', e);
        }
        return 0.50;
    });
    const [deduplicating, setDeduplicating] = useState(false);

    // Save to localStorage whenever threshold changes
    useEffect(() => {
        localStorage.setItem('dedup_threshold', threshold);
    }, [threshold]);

    /**
     * 手动去重
     */
    const handleDeduplicate = async () => {
        setDeduplicating(true);
        try {
            const res = await deduplicateNews(dedupTimeRange, 'mark', threshold, contentType);
            message.success(`去重完成！标记了 ${res.data.stats.duplicates_processed} 条重复新闻, 归档了 ${res.data.stats.archived_count} 条`);
            // 去重会移动数据到本表，刷新列表
            fetchDedupNews(1, dedupPagination.pageSize, dedupFilterSource);
        } catch (e) {
            message.error('去重失败: ' + (e.response?.data?.detail || e.message));
        } finally {
            setDeduplicating(false);
        }
    };


    /**
     * 获取去重数据
     */
    const fetchDedupNews = async (page = 1, pageSize = dedupPagination.pageSize, source = dedupFilterSource, keyword = filterKeyword) => {
        setLoadingDedup(true);
        try {
            const res = await getDeduplicatedNews(page, pageSize, source, keyword, contentType);
            setDedupNews(res.data.data);
            setDedupPagination({
                ...dedupPagination,
                current: page,
                pageSize: pageSize,
                total: res.data.total
            });
        } catch (e) {
            console.error("Fetch dedup news failed", e);
        } finally {
            setLoadingDedup(false);
        }
    };

    /**
     * 删除去重数据
     */
    const handleDeleteDedupNews = async (id) => {
        try {
            await deleteDeduplicatedNews(id);
            message.success('删除成功');
            fetchDedupNews(dedupPagination.current, dedupPagination.pageSize, dedupFilterSource);
        } catch (e) {
            message.error('删除失败');
        }
    };

    /**
     * 还原新闻
     */
    const handleRestoreNews = async (id) => {
        try {
            await restoreNews(id, 'deduplicated_news');
            message.success('还原成功');
            fetchDedupNews(dedupPagination.current, dedupPagination.pageSize, dedupFilterSource);
        } catch (e) {
            message.error('还原失败');
        }
    };

    // 组件加载时获取数据
    useEffect(() => {
        fetchDedupNews(1, dedupPagination.pageSize, dedupFilterSource);
    }, [contentType]);

    // 表格列定义
    // Table columns
    const columns = [
        { title: 'ID', dataIndex: 'id', width: 60 },
        {
            title: '标题',
            dataIndex: 'title',
            ellipsis: true,
            render: (text, record) => <a href={record.source_url} target="_blank" rel="noopener noreferrer">{text}</a>
        },
        { title: '来源', dataIndex: 'source_site', width: 120 },
        {
            title: '发布时间',
            dataIndex: 'published_at',
            width: 160,
            render: text => {
                const date = new Date(text);
                return isNaN(date.getTime()) ? text : date.toLocaleString();
            }
        },
        {
            title: '归档时间',
            dataIndex: 'deduplicated_at',
            width: 160,
            render: text => {
                if (!text) return '-';
                const date = new Date(text);
                return isNaN(date.getTime()) ? text : date.toLocaleString();
            }
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
                    <Button
                        type="link"
                        size="small"
                        onClick={() => handleRestoreNews(record.id)}
                    >
                        还原
                    </Button>
                    <Button
                        type="link"
                        danger
                        size="small"
                        onClick={() => handleDeleteDedupNews(record.id)}
                    >
                        删除
                    </Button>
                </Space>
            )
        }
    ];

    return (
        <>
            <NewsToolbar
                onSearch={(val) => {
                    setFilterKeyword(val);
                    fetchDedupNews(1, dedupPagination.pageSize, dedupFilterSource, val);
                }}
                spiders={spiders}
                selectedSource={dedupFilterSource}
                onSourceChange={(val) => {
                    setDedupFilterSource(val);
                    fetchDedupNews(1, dedupPagination.pageSize, val, filterKeyword);
                }}
                onExport={() => onShowExport && onShowExport('deduplicated')}
                onRefresh={() => fetchDedupNews(dedupPagination.current, dedupPagination.pageSize, dedupFilterSource, filterKeyword)}
                loading={loadingDedup}
            >
                <Space>
                    <span>相似度阈值:</span>
                    <InputNumber
                        min={0.1}
                        max={1.0}
                        step={0.05}
                        value={threshold}
                        onChange={setThreshold}
                        style={{ width: 70 }}
                    />
                    <div style={{ width: 16, display: 'inline-block' }} /> {/* Spacer */}
                    <span>去重范围:</span>
                    <TimeRangeSelect value={dedupTimeRange} onChange={setDedupTimeRange} />
                    <Button
                        type="primary"
                        onClick={handleDeduplicate}
                        loading={deduplicating}
                    >
                        手动去重
                    </Button>
                </Space>
                <div style={{ borderLeft: '1px solid #d9d9d9', height: 24, margin: '0 8px', display: 'inline-block', verticalAlign: 'middle' }} />
                <BatchRestoreButton onSuccess={() => fetchDedupNews(1)} contentType={contentType} />
            </NewsToolbar>

            <Table
                columns={columns}
                dataSource={dedupNews}
                rowKey="id"
                loading={loadingDedup}
                pagination={getPaginationConfig(
                    dedupPagination,
                    (page, pageSize) => fetchDedupNews(page, pageSize, dedupFilterSource, filterKeyword),
                    (page, pageSize) => fetchDedupNews(1, pageSize, dedupFilterSource, filterKeyword)
                )}
                expandable={{
                    expandedRowRender: record => <NewsExpandedView record={record} />,
                    rowExpandable: record => true,
                }}
            />
        </>
    );
};

DeduplicatedTab.propTypes = {
    spiders: PropTypes.arrayOf(PropTypes.object),
    onAddToFeatured: PropTypes.func,
    onShowExport: PropTypes.func,
    contentType: PropTypes.string
};

export default DeduplicatedTab;
