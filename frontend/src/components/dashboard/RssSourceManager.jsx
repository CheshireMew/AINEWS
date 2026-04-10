import React, { useMemo, useState } from 'react';
import PropTypes from 'prop-types';
import { Button, Card, Form, Input, InputNumber, Modal, Popconfirm, Select, Space, Switch, Table, Tag } from 'antd';

const parserOptions = [
    { value: 'generic', label: '标准 RSS/Atom' },
    { value: 'summary_source_link', label: '摘要里的来源链接' },
];

const defaultValues = {
    slug: '',
    display_name: '',
    feed_url: '',
    site_url: '',
    content_kind: 'article',
    parser_type: 'generic',
    default_limit: 20,
    default_interval: 240,
    enabled: true,
};

export default function RssSourceManager({ sources, contentKind, onCreate, onUpdate, onDelete }) {
    const [open, setOpen] = useState(false);
    const [editing, setEditing] = useState(null);
    const [saving, setSaving] = useState(false);
    const [form] = Form.useForm();

    const visibleSources = useMemo(
        () => sources.filter((source) => source.content_kind === contentKind),
        [contentKind, sources],
    );

    const openCreate = () => {
        setEditing(null);
        form.setFieldsValue({ ...defaultValues, content_kind: contentKind });
        setOpen(true);
    };

    const openEdit = (source) => {
        setEditing(source);
        form.setFieldsValue({
            slug: source.slug,
            display_name: source.display_name,
            feed_url: source.feed_url,
            site_url: source.site_url,
            content_kind: source.content_kind,
            parser_type: source.parser_type,
            default_limit: source.default_limit,
            default_interval: source.default_interval,
            enabled: Boolean(source.enabled),
        });
        setOpen(true);
    };

    const closeModal = () => {
        setOpen(false);
        setEditing(null);
        form.resetFields();
    };

    const submit = async () => {
        const values = await form.validateFields();
        setSaving(true);
        try {
            if (editing) {
                await onUpdate(editing.id, values);
            } else {
                await onCreate(values);
            }
            closeModal();
        } finally {
            setSaving(false);
        }
    };

    const columns = [
        {
            title: '名称',
            dataIndex: 'display_name',
            key: 'display_name',
        },
        {
            title: '地址',
            dataIndex: 'feed_url',
            key: 'feed_url',
            render: (value) => <a href={value} target="_blank" rel="noreferrer">{value}</a>,
        },
        {
            title: '解析',
            dataIndex: 'parser_type',
            key: 'parser_type',
            render: (value) => parserOptions.find((option) => option.value === value)?.label || value,
        },
        {
            title: '状态',
            dataIndex: 'enabled',
            key: 'enabled',
            render: (enabled) => <Tag color={enabled ? 'success' : 'default'}>{enabled ? '启用' : '停用'}</Tag>,
        },
        {
            title: '操作',
            key: 'actions',
            render: (_, source) => (
                <Space>
                    <Button size="small" onClick={() => openEdit(source)}>编辑</Button>
                    <Popconfirm title="删除这个 RSS 源？" onConfirm={() => onDelete(source.id)}>
                        <Button size="small" danger>删除</Button>
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    return (
        <Card
            title="RSS 源"
            extra={<Button type="primary" onClick={openCreate}>新增 RSS 源</Button>}
            style={{ marginBottom: 16 }}
        >
            <Table
                rowKey="id"
                size="small"
                pagination={false}
                dataSource={visibleSources}
                columns={columns}
                locale={{ emptyText: '当前内容类型还没有 RSS 源' }}
            />

            <Modal
                open={open}
                title={editing ? '编辑 RSS 源' : '新增 RSS 源'}
                onOk={submit}
                onCancel={closeModal}
                confirmLoading={saving}
                destroyOnHidden
            >
                <Form form={form} layout="vertical" initialValues={{ ...defaultValues, content_kind: contentKind }}>
                    <Form.Item name="display_name" label="名称" rules={[{ required: true, message: '请输入名称' }]}>
                        <Input />
                    </Form.Item>
                    <Form.Item name="slug" label="标识">
                        <Input placeholder="留空时按名称自动生成" />
                    </Form.Item>
                    <Form.Item name="feed_url" label="RSS 地址" rules={[{ required: true, message: '请输入 RSS 地址' }]}>
                        <Input />
                    </Form.Item>
                    <Form.Item name="site_url" label="站点地址" rules={[{ required: true, message: '请输入站点地址' }]}>
                        <Input />
                    </Form.Item>
                    <Form.Item name="content_kind" label="内容类型" rules={[{ required: true, message: '请选择内容类型' }]}>
                        <Select
                            options={[
                                { value: 'news', label: '快讯' },
                                { value: 'article', label: '文章' },
                            ]}
                        />
                    </Form.Item>
                    <Form.Item name="parser_type" label="解析方式" rules={[{ required: true, message: '请选择解析方式' }]}>
                        <Select options={parserOptions} />
                    </Form.Item>
                    <Form.Item name="default_limit" label="默认条数" rules={[{ required: true, message: '请输入默认条数' }]}>
                        <InputNumber min={1} max={100} style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item name="default_interval" label="默认频率(分钟)" rules={[{ required: true, message: '请输入默认频率' }]}>
                        <InputNumber min={5} max={10080} style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item name="enabled" label="启用" valuePropName="checked">
                        <Switch />
                    </Form.Item>
                </Form>
            </Modal>
        </Card>
    );
}

RssSourceManager.propTypes = {
    sources: PropTypes.arrayOf(PropTypes.object).isRequired,
    contentKind: PropTypes.string.isRequired,
    onCreate: PropTypes.func.isRequired,
    onUpdate: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
};
