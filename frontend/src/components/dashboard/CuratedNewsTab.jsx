
import React, { useState, useEffect } from 'react';
import usePaginationConfig from '../common/usePaginationConfig';
import PropTypes from 'prop-types';
import { Table, Button, Space, message, Popconfirm, Tag } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { getDeduplicatedNews, deleteDeduplicatedNews } from '../../api';
import NewsExpandedView from './NewsExpandedView';
import NewsToolbar from './NewsToolbar';


/**
 * 精选数据Tab组件 (现已改为显示 "已去重(通过)/Passed Filters" 数据)
 * 显示所有通过了去重和过滤的新闻，作为精选候选池
 */
const CuratedNewsTab = ({ spiders, onAddToFeatured, onShowExport, active, contentType }) => {
    const { getPaginationConfig } = usePaginationConfig();
    // 状态管理
    const [curatedNews, setCuratedNews] = useState([]);
    const [loadingCurated, setLoadingCurated] = useState(false);
    const [curatedPagination, setCuratedPagination] = useState({ current: 1, pageSize: 10, total: 0 });
    // Deduplicated endpoint doesn't support source yet, but leaving state for future
    const [curatedFilterSource, setCuratedFilterSource] = useState(undefined);
    const [filterKeyword, setFilterKeyword] = useState('');

    /**
     * 获取精选数据 (实际获取 Deduplicated News - Verified only using stage param)
     */
    const fetchCuratedNews = async (page = 1, pageSize = curatedPagination.pageSize, source = curatedFilterSource, keyword = filterKeyword) => {
        setLoadingCurated(true);
        try {
            // 调用 getDeduplicatedNews 并传入 stage='verified'
            const res = await getDeduplicatedNews(page, pageSize, source, keyword, contentType, 'verified');
            setCuratedNews(res.data.data);
            setCuratedPagination({
                ...curatedPagination,
                current: page,
                pageSize: pageSize,
                total: res.data.total
            });
        } catch (e) {
            console.error("Fetch curated (verified) news failed", e);
        } finally {
            setLoadingCurated(false);
        }
    };

    /**
     * 删除数据 (从去重池删除)
     */
    const handleDeleteCuratedNews = async (id) => {
        try {
            await deleteDeduplicatedNews(id);
            message.success('删除成功');
            fetchCuratedNews(curatedPagination.current, curatedPagination.pageSize, curatedFilterSource, filterKeyword);
        } catch (e) {
            message.error('删除失败');
        }
    };

    // 组件加载时获取数据
    useEffect(() => {
        fetchCuratedNews(1, curatedPagination.pageSize, curatedFilterSource);
    }, [contentType, curatedPagination.pageSize]);

    // 激活时刷新数据
    useEffect(() => {
        if (active) {
            fetchCuratedNews(curatedPagination.current, curatedPagination.pageSize, curatedFilterSource, filterKeyword);
        }
    }, [active, curatedPagination.current, curatedPagination.pageSize, curatedFilterSource, filterKeyword]);

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
                        danger
                        size="small"
                        onClick={() => handleDeleteCuratedNews(record.id)}
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
                    fetchCuratedNews(1, curatedFilterSource, val);
                }}
                spiders={spiders}
                selectedSource={curatedFilterSource}
                onSourceChange={(val) => {
                    setCuratedFilterSource(val);
                    fetchCuratedNews(1, val, filterKeyword);
                }}
                onExport={() => onShowExport && onShowExport('curated')}
                onRefresh={() => fetchCuratedNews(curatedPagination.current, curatedFilterSource, filterKeyword)}
                loading={loadingCurated}
            />

            <Table
                columns={columns}
                dataSource={curatedNews}
                rowKey="id"
                loading={loadingCurated}
                pagination={{
                    ...curatedPagination,
                    showSizeChanger: false,
                    onChange: (page) => fetchCuratedNews(page, curatedFilterSource, filterKeyword)
                }}
                expandable={{
                    expandedRowRender: record => <NewsExpandedView record={record} />,
                    rowExpandable: record => true,
                }}
            />
        </>
    );
};

CuratedNewsTab.propTypes = {
    spiders: PropTypes.arrayOf(PropTypes.object),
    onAddToFeatured: PropTypes.func,
    onShowExport: PropTypes.func,
    contentType: PropTypes.string
};

export default CuratedNewsTab;
