import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Table, Button, Select, Space, message, Popconfirm } from 'antd';
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import { getDeduplicatedNews, restoreNews, deduplicateNews, deleteDeduplicatedNews, batchRestoreDeduplicated } from '../../api';
import NewsExpandedView from './NewsExpandedView';
import NewsToolbar from './NewsToolbar';

const { Option } = Select;

/**
 * 去重数据Tab组件
 * 用于管理已去重的新闻数据
 */
const DeduplicatedTab = ({ spiders, onAddToFeatured, onShowExport }) => {
    // 状态管理
    const [dedupNews, setDedupNews] = useState([]);
    const [loadingDedup, setLoadingDedup] = useState(false);
    const [dedupPagination, setDedupPagination] = useState({ current: 1, pageSize: 10, total: 0 });
    const [dedupFilterSource, setDedupFilterSource] = useState(undefined);
    const [filterKeyword, setFilterKeyword] = useState('');


    /**
     * 获取去重数据
     */
    const fetchDedupNews = async (page = 1, source = dedupFilterSource, keyword = filterKeyword) => {
        setLoadingDedup(true);
        try {
            const res = await getDeduplicatedNews(page, 10, source, keyword);
            setDedupNews(res.data.data);
            setDedupPagination({
                ...dedupPagination,
                current: page,
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
            fetchDedupNews(dedupPagination.current, dedupFilterSource);
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
            fetchDedupNews(dedupPagination.current, dedupFilterSource);
        } catch (e) {
            message.error('还原失败');
        }
    };

    // 组件加载时获取数据
    useEffect(() => {
        fetchDedupNews(1, dedupFilterSource);
    }, []);

    // 表格列定义
    /**
     * 批量还原所有已处理的去重数据
     */
    const handleBatchRestore = async () => {
        try {
            const res = await batchRestoreDeduplicated();
            message.success(`批量还原成功！还原了 ${res.data.restored_count} 条数据`);
            fetchDedupNews(1);
        } catch (e) {
            message.error('批量还原失败: ' + (e.response?.data?.detail || e.message));
        }
    };

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
                    fetchDedupNews(1, dedupFilterSource, val);
                }}
                spiders={spiders}
                selectedSource={dedupFilterSource}
                onSourceChange={(val) => {
                    setDedupFilterSource(val);
                    fetchDedupNews(1, val, filterKeyword);
                }}
                onExport={() => onShowExport && onShowExport('deduplicated')}
                onRefresh={() => fetchDedupNews(dedupPagination.current, dedupFilterSource, filterKeyword)}
                loading={loadingDedup}
            >
                <Popconfirm
                    title="还原已去重数据"
                    description="确定要还原所有已处理的去重数据吗？这将把数据还原到 news 表的 'raw' 状态，并删除去重记录和精选记录。"
                    onConfirm={handleBatchRestore}
                    okText="确定"
                    cancelText="取消"
                >
                    <Button type="primary" danger>
                        还原已去重数据
                    </Button>
                </Popconfirm>
            </NewsToolbar>

            <Table
                columns={columns}
                dataSource={dedupNews}
                rowKey="id"
                loading={loadingDedup}
                pagination={{
                    ...dedupPagination,
                    showSizeChanger: false,
                    onChange: (page) => fetchDedupNews(page, dedupFilterSource, filterKeyword)
                }}
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
    onShowExport: PropTypes.func
};

export default DeduplicatedTab;
