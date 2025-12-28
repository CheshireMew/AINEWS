import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Table, Button, Select, Space, Tag, message, Popconfirm } from 'antd';
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import { getNews, deleteNews } from '../../api';
import NewsExpandedView from './NewsExpandedView';
import NewsToolbar from './NewsToolbar';
import usePaginationConfig from '../common/usePaginationConfig';



/**
 * 数据管理Tab组件
 * 用于管理所有原始新闻数据（平铺展示）
 */
const NewsManagementTab = ({ spiders, onShowExport }) => {
    // 状态管理
    const [news, setNews] = useState([]);
    const [loading, setLoading] = useState(false);
    const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });
    const [filterSource, setFilterSource] = useState(undefined);
    const [filterKeyword, setFilterKeyword] = useState('');

    // 使用通用分页配置
    const { getPaginationConfig } = usePaginationConfig(20);

    /**
     * 获取新闻数据
     */
    const fetchNews = async (page = 1, pageSize = pagination.pageSize, source = filterSource, keyword = filterKeyword) => {
        setLoading(true);
        try {
            const res = await getNews(page, pageSize, source, null, keyword);
            setNews(res.data.data);
            setPagination({
                current: page,
                pageSize: pageSize,
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
            fetchNews(pagination.current, pagination.pageSize, filterSource, filterKeyword);
        } catch (e) {
            message.error('删除失败');
        }
    };

    // 组件加载时获取数据
    useEffect(() => {
        fetchNews(1, pagination.pageSize, filterSource, filterKeyword);
    }, []);

    // 表格列定义
    const columns = [
        { title: 'ID', dataIndex: 'id', width: 60 },
        {
            title: '标题',
            dataIndex: 'title',
            ellipsis: true,
            render: (text, record) => (
                <div>
                    <a href={record.source_url} target="_blank" rel="noopener noreferrer">
                        {text}
                    </a>
                    {record.duplicate_of && (
                        <Tag color="orange" style={{ marginLeft: 8 }}>
                            重复于ID:{record.duplicate_of}
                        </Tag>
                    )}
                </div>
            )
        },
        { title: '来源', dataIndex: 'source_site', width: 120 },
        {
            title: '状态',
            dataIndex: 'stage',
            width: 90,
            render: (stage, record) => {
                if (record.duplicate_of) {
                    return <Tag color="orange">重复</Tag>;
                } else {
                    return <Tag color="green">原始</Tag>;
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
                    fetchNews(1, pagination.pageSize, filterSource, val);
                }}
                spiders={spiders}
                selectedSource={filterSource}
                onSourceChange={(val) => {
                    setFilterSource(val);
                    fetchNews(1, pagination.pageSize, val, filterKeyword);
                }}
                onExport={() => onShowExport && onShowExport('raw')}
                onRefresh={() => fetchNews(pagination.current, pagination.pageSize, filterSource, filterKeyword)}
                loading={loading}
            >

            </NewsToolbar>

            <Table
                columns={columns}
                dataSource={news}
                rowKey="id"
                loading={loading}
                pagination={getPaginationConfig(
                    pagination,
                    (page, pageSize) => fetchNews(page, pageSize, filterSource, filterKeyword),
                    (page, pageSize) => fetchNews(page, pageSize, filterSource, filterKeyword)
                )}
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
