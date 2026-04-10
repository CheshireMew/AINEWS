
import React from 'react';
import PropTypes from 'prop-types';
import { Button, Space } from 'antd';

import { useReviewQueueTab } from '../../hooks/dashboard/useReviewQueueTab';
import ContentDataTable from './ContentDataTable';
import { EXPORT_SCOPE } from '../../contracts/content';

const ReviewQueueTab = ({ spiders, onAddToFeatured, onShowExport, active, contentKind }) => {
    const listState = useReviewQueueTab(contentKind, active);

    const columns = [
        { title: 'ID', dataIndex: 'id', width: 60 },
        {
            title: '标题',
            dataIndex: 'title',
            ellipsis: true,
            render: (text, record) => <a href={record.source_url} target="_blank" rel="noopener noreferrer">{text}</a>,
        },
        { title: '来源', dataIndex: 'source_site', width: 120 },
        {
            title: '发布时间',
            dataIndex: 'published_at',
            width: 160,
            render: (text) => {
                const date = new Date(text);
                return Number.isNaN(date.getTime()) ? text : date.toLocaleString();
            },
        },
        {
            title: '操作',
            width: 120,
            render: (_, record) => (
                <Space>
                    <Button type="primary" size="small" onClick={() => onAddToFeatured && onAddToFeatured(record)}>
                        加入输出
                    </Button>
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
            exportScope={EXPORT_SCOPE.REVIEW}
            onShowExport={onShowExport}
        />
    );
};

ReviewQueueTab.propTypes = {
    spiders: PropTypes.arrayOf(PropTypes.object),
    onAddToFeatured: PropTypes.func,
    onShowExport: PropTypes.func,
    active: PropTypes.bool,
    contentKind: PropTypes.string,
};

export default ReviewQueueTab;
