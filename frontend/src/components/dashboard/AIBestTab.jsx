import React, { useState, useEffect } from 'react';
import usePaginationConfig from '../common/usePaginationConfig';
import PropTypes from 'prop-types';
import { Table, Tag, Space, Button, Popconfirm, message, Select } from 'antd';
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import { getFilteredCurated, deleteCuratedNews } from '../../api';
import NewsExpandedView from './NewsExpandedView';
import NewsToolbar from './NewsToolbar';

const { Option } = Select;

/**
 * AI精选Tab组件
 * 显示AI批准的新闻
 */
const AIBestTab = ({ spiders, onAddToFeatured, onShowExport, contentType }) => {
    const { getPaginationConfig } = usePaginationConfig();
    const [approvedNews, setApprovedNews] = useState([]);
    const [approvedLoading, setApprovedLoading] = useState(false);
    const [approvedPagination, setApprovedPagination] = useState({ current: 1, pageSize: 10, total: 0 });
    const [filterSource, setFilterSource] = useState(undefined);
    const [filterKeyword, setFilterKeyword] = useState('');

    /**
     * 加载approved新闻
     */
    const fetchApprovedNews = async (page = 1, pageSize = approvedPagination.pageSize, source = filterSource, keyword = filterKeyword) => {
        setApprovedLoading(true);
        try {
            const res = await getFilteredCurated('approved', page, pageSize, source, keyword, contentType);
            setApprovedNews(res.data.data);
            setApprovedPagination({
                ...approvedPagination,
                current: page,
                pageSize: pageSize,
                total: res.data.total
            });
        } catch (e) {
            message.error('加载失败: ' + (e.response?.data?.detail || e.message));
        } finally {
            setApprovedLoading(false);
        }
    };

    /**
     * 删除approved新闻
     */
    const handleDeleteApproved = async (id) => {
        try {
            await deleteCuratedNews(id);
            message.success('删除成功（已从所有表中永久删除）');
            fetchApprovedNews(approvedPagination.current, approvedPagination.pageSize, filterSource);
        } catch (e) {
            message.error('删除失败: ' + (e.response?.data?.detail || e.message));
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
        {
            title: '发布时间',
            dataIndex: 'published_at',
            width: 160,
            render: text => new Date(text).toLocaleString()
        },
        { title: '来源', dataIndex: 'source_site', width: 100 },
        {
            title: '操作',
            key: 'action',
            width: 150,
            render: (_, record) => (
                <Space>
                    <Button
                        type="primary"
                        size="small"
                        onClick={() => onAddToFeatured && onAddToFeatured(record)}
                    >
                        加精
                    </Button>
                    <Popconfirm title="确定删除?" onConfirm={() => handleDeleteApproved(record.id)}>
                        <Button type="link" danger size="small">删除</Button>
                    </Popconfirm>
                </Space>
            )
        }
    ];

    // 组件加载时获取数据
    useEffect(() => {
        fetchApprovedNews(1, approvedPagination.pageSize, filterSource);
    }, [contentType]);

    return (
        <div style={{ padding: '0 10px' }}>
            {/* 顶部工具栏 (平铺布局) */}
            {/* 顶部工具栏 (平铺布局) */}
            <NewsToolbar
                onSearch={(val) => {
                    setFilterKeyword(val);
                    fetchApprovedNews(1, approvedPagination.pageSize, filterSource, val);
                }}
                spiders={spiders}
                selectedSource={filterSource}
                onSourceChange={(val) => {
                    setFilterSource(val);
                    fetchApprovedNews(1, approvedPagination.pageSize, val, filterKeyword);
                }}
                onExport={() => onShowExport && onShowExport('curated')}
                onRefresh={() => fetchApprovedNews(approvedPagination.current, approvedPagination.pageSize, filterSource, filterKeyword)}
                loading={approvedLoading}
            />

            <Table
                dataSource={approvedNews}
                columns={columns}
                rowKey="id"
                loading={approvedLoading}
                pagination={getPaginationConfig(
                    approvedPagination,
                    (page, pageSize) => fetchApprovedNews(page, pageSize, filterSource, filterKeyword),
                    (page, pageSize) => fetchApprovedNews(1, pageSize, filterSource, filterKeyword)
                )}
                expandable={{
                    expandedRowRender: record => <NewsExpandedView record={record} />,
                    rowExpandable: record => true,
                }}
            />
        </div>
    );
};

AIBestTab.propTypes = {
    spiders: PropTypes.arrayOf(PropTypes.object),
    onAddToFeatured: PropTypes.func,
    onShowExport: PropTypes.func,
    contentType: PropTypes.string
};

export default AIBestTab;
