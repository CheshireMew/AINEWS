import React from 'react';
import PropTypes from 'prop-types';
import { Tag, Space, Button, Popconfirm } from 'antd';

import { useSelectedContentTab } from '../../hooks/dashboard/useSelectedContentTab';
import ContentDataTable from './ContentDataTable';
import { EXPORT_SCOPE } from '../../contracts/content';

const SelectedContentTab = ({ spiders, onAddToFeatured, onShowExport, contentKind }) => {
    const listState = useSelectedContentTab(contentKind);
    const { deleteItem } = listState;

    const columns = [
        { title: 'ID', dataIndex: 'id', width: 60 },
        {
            title: '标题',
            dataIndex: 'title',
            render: (text, record) => <a href={record.source_url} target="_blank" rel="noopener noreferrer">{text}</a>,
        },
        {
            title: '审核结果',
            width: 220,
            render: (_, record) => (
                <span>
                    <Tag color="blue">{record.review_score ?? 0}分</Tag>
                    {record.review_category && <Tag color="green">{record.review_category}</Tag>}
                    <span style={{ color: '#666', marginRight: 4 }}>{record.review_reason || '-'}</span>
                </span>
            ),
        },
        {
            title: '发布时间',
            dataIndex: 'published_at',
            width: 160,
            render: (text) => new Date(text).toLocaleString(),
        },
        { title: '来源', dataIndex: 'source_site', width: 100 },
        {
            title: '操作',
            key: 'action',
            width: 170,
            render: (_, record) => (
                <Space>
                    <Button type="primary" size="small" onClick={() => onAddToFeatured && onAddToFeatured(record)}>
                        加入输出
                    </Button>
                    <Popconfirm title="确定删除?" onConfirm={() => deleteItem(record.id)}>
                        <Button type="link" danger size="small">删除</Button>
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    return (
        <ContentDataTable
            listState={listState}
            columns={columns}
            spiders={spiders}
            contentKind={contentKind}
            exportScope={EXPORT_SCOPE.SELECTED}
            onShowExport={onShowExport}
            wrapperStyle={{ padding: '0 10px' }}
        />
    );
};

SelectedContentTab.propTypes = {
    spiders: PropTypes.arrayOf(PropTypes.object),
    onAddToFeatured: PropTypes.func,
    onShowExport: PropTypes.func,
    contentKind: PropTypes.string,
};

export default SelectedContentTab;
