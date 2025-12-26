import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Table, Button, Select, Space, Tag, message, Popconfirm } from 'antd';
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import { getNews, deleteNews, deduplicateNews } from '../../api';
import NewsExpandedView from './NewsExpandedView';
import NewsToolbar from './NewsToolbar';

const { Option } = Select;

/**
 * 数据管理Tab组件
 * 用于管理原始新闻数据
 */
const NewsManagementTab = ({ spiders, onShowExport }) => {
    // 状态管理
    const [news, setNews] = useState([]);
    const [loading, setLoading] = useState(false);
    const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
    const [filterSource, setFilterSource] = useState(undefined);
    const [filterKeyword, setFilterKeyword] = useState('');
    const [dedupTimeRange, setDedupTimeRange] = useState(6);
    const [deduplicating, setDeduplicating] = useState(false);

    /**
     * 获取新闻数据
     */
    const fetchNews = async (page = 1, source = filterSource, keyword = filterKeyword) => {
        setLoading(true);
        try {
            const res = await getNews(page, 10, source, null, keyword);
            setNews(res.data.data);
            setPagination({
                ...pagination,
                current: page,
                total: res.data.total
            });
        } catch (e) {
            console.error("Fetch news failed", e);
        } finally {
            setLoading(false);
        }
    };

    /**
     * 删除新闻
     */
    const handleDeleteNews = async (id) => {
        try {
            await deleteNews(id);
            message.success('删除成功');
            fetchNews(pagination.current, filterSource);
        } catch (e) {
            message.error('删除失败');
        }
    };

    /**
     * 手动去重
     */
    const handleDeduplicate = async () => {
        setDeduplicating(true);
        try {
            const res = await deduplicateNews(dedupTimeRange, 'mark');
            message.success(`去重完成！标记了 ${res.data.stats.duplicates_processed} 条重复新闻, 归档了 ${res.data.stats.archived_count} 条`);
            fetchNews(pagination.current, filterSource);
        } catch (e) {
            message.error('去重失败: ' + (e.response?.data?.detail || e.message));
        } finally {
            setDeduplicating(false);
        }
    };

    // 组件加载时获取数据
    useEffect(() => {
        fetchNews(1, filterSource);
    }, []);

    // 表格列定义
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
            title: '状态',
            dataIndex: 'stage',
            width: 90,
            render: (stage) => {
                if (stage === 'duplicate') {
                    return <Tag color="red">重复</Tag>;
                } else {
                    return <Tag color="default">原始</Tag>;
                }
            }
        },
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
            title: '操作',
            width: 80,
            render: (_, record) => (
                <Button
                    type="link"
                    danger
                    size="small"
                    onClick={() => handleDeleteNews(record.id)}
                >
                    删除
                </Button>
            )
        }
    ];

    return (
        <>
            <NewsToolbar
                onSearch={(val) => {
                    setFilterKeyword(val);
                    fetchNews(1, filterSource, val);
                }}
                spiders={spiders}
                selectedSource={filterSource}
                onSourceChange={(val) => {
                    setFilterSource(val);
                    fetchNews(1, val, filterKeyword);
                }}
                onExport={() => onShowExport && onShowExport('raw')}
                onRefresh={() => fetchNews(pagination.current, filterSource, filterKeyword)}
                loading={loading}
            >
                <div style={{ borderLeft: '1px solid #d9d9d9', height: 24, margin: '0 8px' }} />
                <span style={{ fontSize: 14 }}>去重范围:</span>
                <Select
                    value={dedupTimeRange}
                    style={{ width: 110 }}
                    onChange={setDedupTimeRange}
                >
                    <Option value={0}>全部</Option>
                    <Option value={6}>6小时内</Option>
                    <Option value={12}>12小时内</Option>
                    <Option value={24}>24小时内</Option>
                    <Option value={48}>48小时内</Option>
                    <Option value={72}>3天内</Option>
                    <Option value={168}>7天内</Option>
                </Select>
                <Button
                    type="primary"
                    onClick={handleDeduplicate}
                    loading={deduplicating}
                >
                    手动去重
                </Button>
            </NewsToolbar>

            <Table
                columns={columns}
                dataSource={news}
                rowKey="id"
                loading={loading}
                pagination={{
                    ...pagination,
                    onChange: (page) => fetchNews(page, filterSource, filterKeyword)
                }}
                expandable={{
                    expandedRowRender: record => <NewsExpandedView record={record} />,
                    rowExpandable: record => true,
                }}
            />
        </>
    );
};

NewsManagementTab.propTypes = {
    onAddToFeatured: PropTypes.func,
    spiders: PropTypes.arrayOf(PropTypes.shape({
        name: PropTypes.string,
        url: PropTypes.string
    })),
    onShowExport: PropTypes.func
};

export default NewsManagementTab;
