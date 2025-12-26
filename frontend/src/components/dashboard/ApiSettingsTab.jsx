
import React, { useState, useEffect } from 'react';
import { Card, Button, Input, Select, Space, message, Form, Switch, Row, Col } from 'antd';
import { SaveOutlined, ApiOutlined, SendOutlined } from '@ant-design/icons';
import {
    getTelegramConfig, setTelegramConfig, testTelegramPush,
    getDeepSeekConfig, setDeepSeekConfig, testDeepSeekConnection
} from '../../api';

const { Option } = Select;

const ApiSettingsTab = () => {
    // DeepSeek 配置状态
    const [deepseekConfig, setDeepSeekConfigState] = useState({ api_key: '', base_url: 'https://api.deepseek.com', model: 'deepseek-chat' });

    // Telegram 配置状态
    const [telegramConfig, setTelegramConfigState] = useState({ bot_token: '', chat_id: '', enabled: false });

    useEffect(() => {
        fetchDeepSeekConfig();
        fetchTelegramConfig();
    }, []);

    const fetchDeepSeekConfig = async () => {
        try {
            const res = await getDeepSeekConfig();
            setDeepSeekConfigState(res.data);
        } catch (error) {
            console.error("Failed to fetch DeepSeek config", error);
        }
    };

    const fetchTelegramConfig = async () => {
        try {
            const res = await getTelegramConfig();
            setTelegramConfigState(res.data);
        } catch (error) {
            console.error("Failed to fetch Telegram config", error);
        }
    };

    // DeepSeek Handlers
    const handleSaveDeepSeekConfig = async () => {
        try {
            await setDeepSeekConfig(deepseekConfig);
            message.success("DeepSeek 配置已保存");
        } catch (error) {
            message.error("保存失败: " + (error.response?.data?.detail || error.message));
        }
    };

    const handleTestDeepSeekConnection = async () => {
        try {
            await testDeepSeekConnection();
            message.success("连接测试成功！API Key 和 Base URL 配置正确。");
        } catch (error) {
            message.error("连接测试失败: " + (error.response?.data?.detail || error.message));
        }
    };

    // Telegram Handlers
    const handleSaveTelegramConfig = async () => {
        try {
            await setTelegramConfig(telegramConfig);
            message.success("Telegram 配置已保存");
        } catch (error) {
            message.error("保存失败: " + (error.response?.data?.detail || error.message));
        }
    };

    const handleTestTelegramPush = async () => {
        try {
            await testTelegramPush();
            message.success("测试消息发送成功，请检查 Telegram");
        } catch (error) {
            message.error("测试发送失败: " + (error.response?.data?.detail || error.message));
        }
    };

    return (
        <div style={{ padding: '0 10px' }}>
            <h3>全局 API 配置</h3>
            <Row gutter={16}>
                <Col xs={24} md={12}>
                    <Card title={<Space><ApiOutlined /> DeepSeek AI 配置</Space>} style={{ marginBottom: 20 }}>
                        <Form layout="vertical">
                            <Form.Item label="API Key">
                                <Input.Password
                                    value={deepseekConfig.api_key}
                                    onChange={e => setDeepSeekConfigState({ ...deepseekConfig, api_key: e.target.value })}
                                    placeholder="sk-..."
                                />
                            </Form.Item>
                            <Form.Item label="Base URL">
                                <Input
                                    value={deepseekConfig.base_url}
                                    onChange={e => setDeepSeekConfigState({ ...deepseekConfig, base_url: e.target.value })}
                                    placeholder="https://api.deepseek.com"
                                />
                            </Form.Item>
                            <Form.Item label="Model">
                                <Select
                                    value={deepseekConfig.model}
                                    onChange={(value) => {
                                        let newBaseUrl = deepseekConfig.base_url;
                                        if (value === 'deepseek-chat' || value === 'deepseek-reasoner') {
                                            newBaseUrl = 'https://api.deepseek.com';
                                        } else if (value.startsWith('gpt-')) {
                                            newBaseUrl = 'https://api.openai.com/v1';
                                        } else if (value.startsWith('claude-')) {
                                            newBaseUrl = 'https://api.anthropic.com/v1';
                                        }
                                        setDeepSeekConfigState({ ...deepseekConfig, model: value, base_url: newBaseUrl });
                                    }}
                                    placeholder="选择或输入模型"
                                >
                                    <Option value="deepseek-chat">deepseek-chat</Option>
                                    <Option value="deepseek-reasoner">deepseek-reasoner</Option>
                                    <Option value="gpt-4o">gpt-4o</Option>
                                    <Option value="gpt-4o-mini">gpt-4o-mini</Option>
                                    <Option value="claude-3-5-sonnet-20240620">claude-3-5-sonnet-20240620</Option>
                                </Select>
                            </Form.Item>
                            <Space>
                                <Button type="primary" icon={<SaveOutlined />} onClick={handleSaveDeepSeekConfig}>保存配置</Button>
                                <Button onClick={handleTestDeepSeekConnection}>测试连接</Button>
                            </Space>
                        </Form>
                    </Card>
                </Col>
                <Col xs={24} md={12}>
                    <Card title={<Space><SendOutlined /> Telegram 推送配置</Space>} style={{ marginBottom: 20 }}>
                        <Form layout="vertical">
                            <Form.Item label="Bot Token">
                                <Input.Password
                                    value={telegramConfig.bot_token}
                                    onChange={e => setTelegramConfigState({ ...telegramConfig, bot_token: e.target.value })}
                                    placeholder="123456789:ABCDef..."
                                />
                                <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                                    从 @BotFather 获取
                                </div>
                            </Form.Item>
                            <Form.Item label="Chat ID">
                                <Input
                                    value={telegramConfig.chat_id}
                                    onChange={e => setTelegramConfigState({ ...telegramConfig, chat_id: e.target.value })}
                                    placeholder="@channel_name or -100xxx"
                                />
                                <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                                    目标频道/群组 ID，需先将 Bot 拉入并设为管理员
                                </div>
                            </Form.Item>
                            <Form.Item label="启用推送">
                                <Switch
                                    checked={telegramConfig.enabled}
                                    onChange={checked => setTelegramConfigState({ ...telegramConfig, enabled: checked })}
                                />
                                <span style={{ marginLeft: 8, color: '#999' }}>(仅推送 "精选数据")</span>
                            </Form.Item>
                            <Space>
                                <Button type="primary" icon={<SaveOutlined />} onClick={handleSaveTelegramConfig}>保存配置</Button>
                                <Button onClick={handleTestTelegramPush}>测试发送</Button>
                            </Space>
                        </Form>
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

export default ApiSettingsTab;
