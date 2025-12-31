import React, { useState, useEffect } from 'react';
import usePaginationConfig from '../common/usePaginationConfig';
import PropTypes from 'prop-types';
import { Card, Button, Select, Input, Table, Space, message, Popconfirm, Divider } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import {
    getBlacklist, addBlacklist, deleteBlacklist, filterNews, getFilteredDedupNews, restoreNews, deleteDeduplicatedNews, batchRestoreFiltered
} from '../../api';
import NewsExpandedView from './NewsExpandedView';
import NewsToolbar from './NewsToolbar';
import TimeRangeSelect from './TimeRangeSelect';

const { Option } = Select;

/**
 * 过滤设置Tab组件
 * 用于管理黑名单关键词和查看被过滤的新闻
 */
const FilterSettingsTab = ({ onAddToFeatured, active, contentType }) => {
    const { getPaginationConfig } = usePaginationConfig();
    // 本地过滤状态
    const [filterTimeRange, setFilterTimeRange] = useState(6);
    const [filtering, setFiltering] = useState(false);

    // 黑名单状态
    const [blacklistKeywords, setBlacklistKeywords] = useState([]);
    const [newKeyword, setNewKeyword] = useState('');
    const [newMatchType, setNewMatchType] = useState('contains');

    // 已过滤新闻状态
    const [filteredNews, setFilteredNews] = useState([]);
    const [loadingFiltered, setLoadingFiltered] = useState(false);
    const [filteredPagination, setFilteredPagination] = useState({ current: 1, pageSize: 10, total: 0 });
    const [filterKeyword, setFilterKeyword] = useState('');

    // 组件加载时获取数据
    useEffect(() => {
        fetchBlacklistData();
        fetchFilteredNews(1, filteredPagination.pageSize);
    }, []);

    // 激活时刷新数据
    useEffect(() => {
        if (active) {
            fetchBlacklistData();
            fetchFilteredNews(filteredPagination.current, filteredPagination.pageSize, filterKeyword);
        }
    }, [active]);

    // contentType 变化时刷新数据
    useEffect(() => {
        fetchFilteredNews(1, filteredPagination.pageSize);
    }, [contentType]);

    /**
     * 获取黑名单数据
     */
    const fetchBlacklistData = async () => {
        try {
            const res = await getBlacklist(contentType);
            setBlacklistKeywords(res.data.keywords || []);
        } catch (e) {
            console.error("Fetch blacklist failed", e);
        }
    };

    /**
     * 添加黑名单关键词
     */
    const handleAddKeyword = async () => {
        if (!newKeyword.trim()) return;
        try {
            await addBlacklist(newKeyword.trim(), newMatchType, contentType);
            message.success('添加成功');
            setNewKeyword('');
            fetchBlacklistData();
        } catch (e) {
            message.error('添加失败');
        }
    };

    /**
     * 删除黑名单关键词
     */
    const handleDeleteKeyword = async (id) => {
        try {
            await deleteBlacklist(id);
            message.success('删除成功');
            fetchBlacklistData();
        } catch (e) {
            message.error('删除失败');
        }
    };

    /**
     * 执行本地过滤
     */
    const handleFilterNews = async () => {
        setFiltering(true);
        try {
            const res = await filterNews(filterTimeRange, contentType);
            const stats = res.data.stats;
            message.success(`过滤完成！共扫描 ${stats.scanned} 条：过滤 ${stats.filtered} 条，通过 ${stats.curated || 0} 条`);
            // 刷新已过滤列表以显示新过滤的数据
            fetchFilteredNews(1, filteredPagination.pageSize);
        } catch (e) {
            message.error('过滤失败: ' + (e.response?.data?.detail || e.message));
        } finally {
            setFiltering(false);
        }
    };

    /**
     * 批量还原所有已过滤的数据
     */
    const handleBatchRestoreFiltered = async () => {
        try {
            const res = await batchRestoreFiltered(contentType);
            message.success(`批量还原成功！还原了 ${res.data.restored_count} 条数据`);
            fetchFilteredNews(1, filteredPagination.pageSize);
        } catch (e) {
            message.error('批量还原失败: ' + (e.response?.data?.detail || e.message));
        }
    };

    /**
     * 获取已过滤新闻
     */
    const fetchFilteredNews = async (page = 1, pageSize = filteredPagination.pageSize, keyword = filterKeyword) => {
        setLoadingFiltered(true);
        try {
            const res = await getFilteredDedupNews(page, pageSize, keyword, contentType);
            setFilteredNews(res.data.data);
            setFilteredPagination({
                ...filteredPagination,
                current: page,
                pageSize: pageSize,
                total: res.data.total
            });
        } catch (e) {
            console.error("Fetch filtered news failed", e);
        } finally {
            setLoadingFiltered(false);
        }
    };

    /**
     * 还原已过滤新闻
     */
    const handleRestoreNews = async (id) => {
        try {
            await restoreNews(id, 'deduplicated_news');
            message.success('还原成功');
            fetchFilteredNews(filteredPagination.current);
        } catch (e) {
            message.error('还原失败');
        }
    };

    // 黑名单表格列定义
    const blacklistColumns = [
        { title: '关键词', dataIndex: 'keyword', key: 'keyword' },
        {
            title: '匹配类型',
            dataIndex: 'match_type',
            key: 'match_type',
            render: (text) => text === 'contains' ? '包含' : '正则'
        },
        {
            title: '操作',
            key: 'action',
            render: (_, record) => (
                <Popconfirm title="确定删除?" onConfirm={() => handleDeleteKeyword(record.id)}>
                    <Button type="link" danger>删除</Button>
                </Popconfirm>
            )
        }
    ];

    /**
     * 删除已过滤新闻
     */
    const handleDeleteFilteredNews = async (id) => {
        try {
            await deleteDeduplicatedNews(id);
            message.success('删除成功');
            fetchFilteredNews(filteredPagination.current);
        } catch (e) {
            message.error('删除失败');
        }
    };

    // 已过滤新闻表格列定义
    const filteredColumns = [
        { title: 'ID', dataIndex: 'id', width: 60 },
        {
            title: '标题',
            dataIndex: 'title',
            render: (text, record) => <a href={record.source_url} target="_blank" rel="noopener noreferrer">{text}</a>
        },
        {
            title: '过滤原因',
            dataIndex: 'keyword_filter_reason',
            width: 150,
            render: (text) => text || '-'
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
                    <Button
                        type="link"
                        size="small"
                        onClick={() => handleRestoreNews(record.id)}
                    >
                        还原
                    </Button>
                    <Popconfirm title="确定删除?" onConfirm={() => handleDeleteFilteredNews(record.id)}>
                        <Button type="link" danger size="small">删除</Button>
                    </Popconfirm>
                </Space>
            )
        }
    ];

    return (
        <div style={{ padding: '0 10px' }}>
            {/* 1. 执行本地过滤 */}
            <div style={{ marginBottom: 20 }}>
                <h3>1. 执行本地过滤 (关键词黑名单)</h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                    <TimeRangeSelect value={filterTimeRange} onChange={setFilterTimeRange} />
                    <Button type="primary" onClick={handleFilterNews} loading={filtering}>
                        立即执行过滤
                    </Button>
                    <Popconfirm
                        title="还原已过滤数据"
                        description="确定要还原所有已过滤/已精选的数据吗？这将把 'filtered'和'verified' 状态的数据都重置为 'deduplicated'，以便重新进行过滤。"
                        onConfirm={handleBatchRestoreFiltered}
                        okText="确定"
                        cancelText="取消"
                    >
                        <Button type="primary" danger>
                            还原已过滤数据
                        </Button>
                    </Popconfirm>
                    <span style={{ color: '#999', fontSize: 13 }}>
                        (注: 仅扫描已去重(deduplicated)的新闻，匹配黑名单则自动归档到下方列表)
                    </span>
                </div>
            </div>

            {/* 2. 黑名单关键词管理 */}
            <div style={{ marginBottom: 20 }}>
                <h3>2. 黑名单关键词管理</h3>
                <div style={{ marginBottom: 16, display: 'flex', gap: 10 }}>
                    <Select value={newMatchType} style={{ width: 100 }} onChange={setNewMatchType}>
                        <Option value="contains">包含</Option>
                        <Option value="regex">正则</Option>
                    </Select>
                    <Input
                        placeholder="输入屏蔽词..."
                        style={{ width: 200 }}
                        value={newKeyword}
                        onChange={e => setNewKeyword(e.target.value)}
                        onPressEnter={handleAddKeyword}
                    />
                    <Button type="primary" onClick={handleAddKeyword} icon={<PlusOutlined />}>添加</Button>
                </div>
                <Table
                    columns={blacklistColumns}
                    dataSource={blacklistKeywords}
                    rowKey="id"
                    pagination={{ pageSize: 10 }}
                    size="small"
                />
            </div>

            <Divider />

            {/* 3. 已过滤新闻 */}
            <div style={{ marginTop: 20 }}>
                <div style={{ marginBottom: 16 }}>
                    <h3>3. 已过滤新闻 (自动屏蔽)</h3>
                    <NewsToolbar
                        onSearch={(val) => {
                            setFilterKeyword(val);
                            fetchFilteredNews(1, filteredPagination.pageSize, val);
                        }}
                        onRefresh={() => fetchFilteredNews(filteredPagination.current, filteredPagination.pageSize, filterKeyword)}
                        loading={loadingFiltered}
                    />
                </div>
                <Table
                    columns={filteredColumns}
                    dataSource={filteredNews}
                    rowKey="id"
                    loading={loadingFiltered}
                    pagination={getPaginationConfig(
                        filteredPagination,
                        (page, pageSize) => fetchFilteredNews(page, pageSize, filterKeyword),
                        (page, pageSize) => fetchFilteredNews(1, pageSize, filterKeyword)
                    )}
                    size="small"
                    expandable={{
                        expandedRowRender: record => <NewsExpandedView record={record} />,
                        rowExpandable: record => true,
                    }}
                />
            </div>
        </div>
    );
};

FilterSettingsTab.propTypes = {
    onAddToFeatured: PropTypes.func
};

export default FilterSettingsTab;
