
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Table, Button, Select, Space, message } from 'antd';
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import { getCuratedNews, deleteCuratedNews, exportNews } from '../../api';
import NewsExpandedView from './NewsExpandedView';
import NewsToolbar from './NewsToolbar';

const { Option } = Select;

/**
 * 精选数据Tab组件
 * 用于管理人工精选的新闻数据
 */
const CuratedNewsTab = ({ spiders, onAddToFeatured, onShowExport }) => {
    // 状态管理
    const [curatedNews, setCuratedNews] = useState([]);
    const [loadingCurated, setLoadingCurated] = useState(false);
    const [curatedPagination, setCuratedPagination] = useState({ current: 1, pageSize: 10, total: 0 });
    const [curatedFilterSource, setCuratedFilterSource] = useState(undefined);
    const [filterKeyword, setFilterKeyword] = useState('');

    /**
     * 获取精选数据
     */
    const fetchCuratedNews = async (page = 1, source = curatedFilterSource, keyword = filterKeyword) => {
        setLoadingCurated(true);
        try {
            const res = await getCuratedNews(page, 10, source, keyword);
            setCuratedNews(res.data.data);
            setCuratedPagination({
                ...curatedPagination,
                current: page,
                total: res.data.total
            });
        } catch (e) {
            console.error("Fetch curated news failed", e);
        } finally {
            setLoadingCurated(false);
        }
    };

    /**
     * 删除精选数据
     */
    const handleDeleteCuratedNews = async (id) => {
        try {
            await deleteCuratedNews(id);
            message.success('删除成功');
            fetchCuratedNews(curatedPagination.current, curatedFilterSource);
        } catch (e) {
            message.error('删除失败');
        }
    };

    // 组件加载时获取数据
    useEffect(() => {
        fetchCuratedNews(1, curatedFilterSource);
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
    onShowExport: PropTypes.func
};

export default CuratedNewsTab;
