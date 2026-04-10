import React from 'react';
import { Button, Card, Form, Input, Select, Space } from 'antd';
import { ApiOutlined, SaveOutlined } from '@ant-design/icons';
import { useAiProviderSettings } from '../../../hooks/dashboard/system-settings/useAiProviderSettings';

export default function AiProviderCard() {
    const { config, setConfig, save, test, handleModelChange } = useAiProviderSettings();

    return (
        <Card title={<Space><ApiOutlined /> AI Provider 配置</Space>} style={{ marginBottom: 20 }}>
            <Form layout="vertical">
                <Form.Item label="API Key">
                    <Input.Password value={config.api_key} onChange={(event) => setConfig((prev) => ({ ...prev, api_key: event.target.value }))} placeholder="sk-..." />
                </Form.Item>
                <Form.Item label="Base URL">
                    <Input value={config.base_url} onChange={(event) => setConfig((prev) => ({ ...prev, base_url: event.target.value }))} placeholder="https://api.deepseek.com" />
                </Form.Item>
                <Form.Item label="Model">
                    <Select value={config.model} onChange={handleModelChange}>
                        <Select.Option value="deepseek-chat">deepseek-chat</Select.Option>
                        <Select.Option value="deepseek-reasoner">deepseek-reasoner</Select.Option>
                        <Select.Option value="gpt-4o">gpt-4o</Select.Option>
                        <Select.Option value="gpt-4o-mini">gpt-4o-mini</Select.Option>
                        <Select.Option value="claude-3-5-sonnet-20240620">claude-3-5-sonnet-20240620</Select.Option>
                    </Select>
                </Form.Item>
                <Space>
                    <Button type="primary" icon={<SaveOutlined />} onClick={save}>保存配置</Button>
                    <Button onClick={test}>测试连接</Button>
                </Space>
            </Form>
        </Card>
    );
}
