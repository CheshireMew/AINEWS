import React from 'react';
import PropTypes from 'prop-types';
import { Button, Select, Input, Table, Popconfirm } from 'antd';

const { Option } = Select;

export default function BlocklistKeywordManager({
    blacklistKeywords,
    newKeyword,
    newMatchType,
    setNewKeyword,
    setNewMatchType,
    addKeyword,
    removeKeyword,
}) {
    const blocklistColumns = [
        { title: '关键词', dataIndex: 'keyword', key: 'keyword' },
        {
            title: '匹配类型',
            dataIndex: 'match_type',
            key: 'match_type',
            render: (text) => text === 'contains' ? '包含' : '正则',
        },
        {
            title: '操作',
            key: 'action',
            render: (_, record) => (
                <Popconfirm title="确定删除?" onConfirm={() => removeKeyword(record.id)}>
                    <Button type="link" danger>删除</Button>
                </Popconfirm>
            ),
        },
    ];

    return (
        <div style={{ marginBottom: 20 }}>
            <h3>2. 黑名单管理</h3>
            <div style={{ marginBottom: 16, display: 'flex', gap: 10 }}>
                <Select value={newMatchType} style={{ width: 100 }} onChange={setNewMatchType}>
                    <Option value="contains">包含</Option>
                    <Option value="regex">正则</Option>
                </Select>
                <Input
                    placeholder="输入屏蔽词..."
                    style={{ width: 200 }}
                    value={newKeyword}
                    onChange={(event) => setNewKeyword(event.target.value)}
                    onPressEnter={addKeyword}
                />
                <Button type="primary" onClick={addKeyword}>添加</Button>
            </div>
            <Table columns={blocklistColumns} dataSource={blacklistKeywords} rowKey="id" pagination={{ pageSize: 10 }} size="small" />
        </div>
    );
}

BlocklistKeywordManager.propTypes = {
    blacklistKeywords: PropTypes.arrayOf(PropTypes.object).isRequired,
    newKeyword: PropTypes.string.isRequired,
    newMatchType: PropTypes.string.isRequired,
    setNewKeyword: PropTypes.func.isRequired,
    setNewMatchType: PropTypes.func.isRequired,
    addKeyword: PropTypes.func.isRequired,
    removeKeyword: PropTypes.func.isRequired,
};
