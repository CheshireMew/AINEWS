import React from 'react';
import PropTypes from 'prop-types';
import { Button, Tag } from 'antd';

import { useIncomingContentTab } from '../../hooks/dashboard/useIncomingContentTab';
import ContentDataTable from './ContentDataTable';
import { EXPORT_SCOPE } from '../../contracts/content';


const NewsManagementTab = ({ spiders, onShowExport, contentKind }) => {
    const listState = useIncomingContentTab(contentKind);
    const { deleteItem } = listState;

    const columns = [
        { title: 'ID', dataIndex: 'id', width: 60 },
        {
            title: '标题',
            dataIndex: 'title',
            ellipsis: true,
            render: (text, record) => (
                <a href={record.source_url} target="_blank" rel="noopener noreferrer">
                    {text}
                </a>
            )
        },
        { title: '来源', dataIndex: 'source_site', width: 120 },
        {
            title: '作者',
            dataIndex: 'author',
            width: 140,
            render: (text) => text || '-'
        },
        {
            title: '状态',
            dataIndex: 'stage',
            width: 90,
            render: () => <Tag color="green">待归档</Tag>
        },
        {
            title: '发布时间',
            dataIndex: 'published_at',
            width: 160,
            render: (text) => {
                const date = new Date(text);
                return Number.isNaN(date.getTime()) ? text : date.toLocaleString();
            }
        },
        {
            title: '操作',
            width: 80,
            render: (_, record) => (
                <Button type="link" danger size="small" onClick={() => deleteItem(record.id)}>
                    删除
                </Button>
            )
        }
    ];

    return (
        <ContentDataTable
            listState={listState}
            columns={columns}
            spiders={spiders}
            contentKind={contentKind}
            exportScope={EXPORT_SCOPE.INCOMING}
            onShowExport={onShowExport}
        />
    );
};

NewsManagementTab.propTypes = {
    spiders: PropTypes.arrayOf(PropTypes.object),
    onShowExport: PropTypes.func,
    contentKind: PropTypes.string,
};

export default NewsManagementTab;
