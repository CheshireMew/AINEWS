import React from 'react';
import PropTypes from 'prop-types';
import { Card, Button, Input, Tag, Space, Popconfirm } from 'antd';

import { useDiscardedContentActions } from '../../hooks/dashboard/useDiscardedContentActions';
import { useDiscardedContentList } from '../../hooks/dashboard/useDiscardedContentList';
import { useReviewRunner } from '../../hooks/dashboard/useReviewRunner';
import { useReviewSettings } from '../../hooks/dashboard/useReviewSettings';
import ContentDataTable from './ContentDataTable';
import TimeRangeSelect from './TimeRangeSelect';

const { TextArea } = Input;

const DiscardedContentTab = ({ onAddToFeatured, contentKind }) => {
    const listState = useDiscardedContentList(contentKind);
    const {
        reviewPrompt,
        reviewHours,
        setReviewPrompt,
        setReviewHours,
        saveSettings,
    } = useReviewSettings(contentKind);
    const {
        running,
        logs,
        runReviewFlow,
    } = useReviewRunner(contentKind, reviewPrompt, reviewHours, listState, saveSettings);
    const {
        requeueItem,
        deleteItem,
        requeueAll,
        clearAll,
    } = useDiscardedContentActions(contentKind, listState);

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
                    {record.review_category && <Tag color="orange">{record.review_category}</Tag>}
                    <span style={{ color: '#666', marginRight: 4 }}>{record.review_reason || '-'}</span>
                </span>
            ),
        },
        { title: '来源', dataIndex: 'source_site', width: 100 },
        {
            title: '发布时间',
            dataIndex: 'published_at',
            width: 160,
            render: (text) => new Date(text).toLocaleString(),
        },
        {
            title: '操作',
            width: 220,
            render: (_, record) => (
                <Space>
                    <Button type="primary" size="small" onClick={() => onAddToFeatured && onAddToFeatured(record)}>
                        加入输出
                    </Button>
                    <Button type="link" onClick={() => requeueItem(record.id)}>还原</Button>
                    <Popconfirm title="确定删除这条内容？" description="此操作将彻底删除对应内容" onConfirm={() => deleteItem(record.id)}>
                        <Button type="link" danger>删除</Button>
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    return (
        <div style={{ padding: '0 10px' }}>
            <Card title="审核配置" style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', gap: 24 }}>
                    <div style={{ flex: 1 }}>
                        <Space direction="vertical" style={{ width: '100%' }}>
                            <div>
                                <div style={{ marginBottom: 8 }}>审核提示词:</div>
                                <TextArea
                                    rows={6}
                                    value={reviewPrompt}
                                    onChange={(event) => setReviewPrompt(event.target.value)}
                                    placeholder="输入审核提示词..."
                                    onBlur={saveSettings}
                                />
                            </div>
                            <Space>
                                <span>扫描范围:</span>
                                <TimeRangeSelect value={reviewHours} onChange={setReviewHours} />
                                <Button type="primary" onClick={runReviewFlow} loading={running}>开始审核</Button>
                                <Button onClick={saveSettings}>保存配置</Button>
                            </Space>
                        </Space>
                    </div>
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                        <div style={{ marginBottom: 8 }}>运行日志:</div>
                        <div style={{ background: '#000', color: '#0f0', padding: '12px', borderRadius: 4, fontSize: 12, height: '240px', overflowY: 'auto', fontFamily: 'monospace', width: '100%' }}>
                            <div style={{ color: '#8c8c8c', marginBottom: 8, borderBottom: '1px solid #333', paddingBottom: 4 }}>
                                &gt; REVIEW LOG
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                {logs.length === 0 && !running ? (
                                    <div style={{ color: '#666' }}>&gt; Ready to run.</div>
                                ) : (
                                    logs.map((log, index) => (
                                        <div key={index} style={{ wordBreak: 'break-all' }}>&gt; {log}</div>
                                    ))
                                )}
                                {running && <div style={{ color: '#aaa', fontStyle: 'italic' }}>... Running ...</div>}
                            </div>
                        </div>
                    </div>
                </div>
            </Card>

            <Card title="已舍弃内容">
                <ContentDataTable
                    listState={{
                        items: listState.items,
                        loading: listState.loading,
                        pagination: listState.pagination,
                        filterKeyword: listState.filterKeyword,
                        setFilterKeyword: listState.setFilterKeyword,
                        fetchItems: listState.fetchItems,
                    }}
                    columns={columns}
                    contentKind={contentKind}
                    showSourceFilter={false}
                    toolbarChildren={(
                        <>
                            <Popconfirm title="确定恢复全部?" description="将把所有已舍弃内容恢复为待审核状态" onConfirm={requeueAll}>
                                <Button>批量恢复</Button>
                            </Popconfirm>
                            <Popconfirm title="确定清除所有审核结果？" description="将把所有已审核内容恢复为待审核状态" onConfirm={clearAll}>
                                <Button danger>清空审核结果</Button>
                            </Popconfirm>
                        </>
                    )}
                />
            </Card>
        </div>
    );
};

DiscardedContentTab.propTypes = {
    onAddToFeatured: PropTypes.func,
    contentKind: PropTypes.string,
};

export default DiscardedContentTab;
