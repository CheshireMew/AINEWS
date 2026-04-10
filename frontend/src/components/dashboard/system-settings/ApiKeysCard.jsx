import React from 'react';
import { Button, Card, Form, Input, Modal, Popconfirm, Space, Table, Typography } from 'antd';
import { CopyOutlined, DeleteOutlined, KeyOutlined, PlusOutlined } from '@ant-design/icons';
import { useApiKeys } from '../../../hooks/dashboard/system-settings/useApiKeys';

const { Text } = Typography;

export default function ApiKeysCard() {
    const {
        apiKeys,
        showCreateModal,
        newKeyName,
        newKeyNotes,
        setShowCreateModal,
        setNewKeyName,
        setNewKeyNotes,
        resetModal,
        createKey,
        deleteKey,
        copyKey,
    } = useApiKeys();

    const columns = [
        { title: '名称', dataIndex: 'key_name', key: 'key_name', width: 150 },
        {
            title: 'API密钥',
            dataIndex: 'api_key',
            key: 'api_key',
            render: (text) => (
                <Input.Password value={text} readOnly style={{ width: 300 }} suffix={<CopyOutlined onClick={() => copyKey(text)} style={{ cursor: 'pointer', color: '#1890ff' }} />} />
            ),
        },
        { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 160 },
        { title: '最后使用', dataIndex: 'last_used_at', key: 'last_used_at', width: 160, render: (text) => text || '未使用' },
        {
            title: '操作',
            key: 'action',
            width: 120,
            render: (_, record) => (
                <Space>
                    <Button size="small" icon={<CopyOutlined />} onClick={() => copyKey(record.api_key)}>复制</Button>
                    <Popconfirm
                        title="确定删除此密钥？"
                        description="删除后使用此密钥的用户将无法访问 API"
                        onConfirm={() => deleteKey(record.id, record.key_name)}
                        okText="确认"
                        cancelText="取消"
                    >
                        <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    return (
        <Card
            title={<Space><KeyOutlined /> 分析师 API 密钥管理</Space>}
            style={{ height: '100%' }}
            extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setShowCreateModal(true)} size="small">新建</Button>}
        >
            <Table dataSource={apiKeys} columns={columns} rowKey="id" pagination={false} locale={{ emptyText: '暂无密钥' }} scroll={{ x: true }} size="small" />
            <div style={{ marginTop: 16, background: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
                <Text strong>使用说明：</Text>
                <ul style={{ marginTop: 8, marginBottom: 0, paddingLeft: 20 }}>
                    <li>为不同用户生成独立密钥</li>
                    <li>密钥可独立删除</li>
                    <li><code>GET /api/analyst/news</code></li>
                </ul>
            </div>

            <Modal title="创建新 API 密钥" open={showCreateModal} onOk={createKey} onCancel={resetModal} okText="创建" cancelText="取消">
                <Form layout="vertical">
                    <Form.Item label="密钥名称" required extra="用于标识此密钥的用途或使用者">
                        <Input value={newKeyName} onChange={(event) => setNewKeyName(event.target.value)} placeholder="请输入密钥名称" />
                    </Form.Item>
                    <Form.Item label="备注（可选）">
                        <Input.TextArea value={newKeyNotes} onChange={(event) => setNewKeyNotes(event.target.value)} placeholder="备注信息" rows={3} />
                    </Form.Item>
                </Form>
            </Modal>
        </Card>
    );
}
