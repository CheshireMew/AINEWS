import React from 'react';
import { Button, Card, Form, Input, Space, Switch } from 'antd';
import { SaveOutlined, SendOutlined } from '@ant-design/icons';
import { useTelegramSettings } from '../../../hooks/dashboard/system-settings/useTelegramSettings';

export default function TelegramSettingsCard() {
    const { config, setConfig, save, test } = useTelegramSettings();

    return (
        <Card title={<Space><SendOutlined /> Telegram 推送配置</Space>} style={{ marginBottom: 20 }}>
            <Form layout="vertical">
                <Form.Item label="Bot Token">
                    <Input.Password value={config.bot_token} onChange={(event) => setConfig((prev) => ({ ...prev, bot_token: event.target.value }))} placeholder="123456789:ABCDef..." />
                    <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>从 @BotFather 获取</div>
                </Form.Item>
                <Form.Item label="Chat ID">
                    <Input value={config.chat_id} onChange={(event) => setConfig((prev) => ({ ...prev, chat_id: event.target.value }))} placeholder="@channel_name or -100xxx" />
                    <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>目标频道/群组 ID，需先将 Bot 拉入并设为管理员</div>
                </Form.Item>
                <Form.Item label="启用推送">
                    <Switch checked={config.enabled} onChange={(enabled) => setConfig((prev) => ({ ...prev, enabled }))} />
                    <span style={{ marginLeft: 8, color: '#999' }}>(仅推送已选入内容)</span>
                </Form.Item>
                <Space>
                    <Button type="primary" icon={<SaveOutlined />} onClick={save}>保存配置</Button>
                    <Button onClick={test}>测试发送</Button>
                </Space>
            </Form>
        </Card>
    );
}
