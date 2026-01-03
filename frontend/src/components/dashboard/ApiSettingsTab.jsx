
import React, { useState, useEffect } from 'react';
import { Card, Button, Input, Select, Space, message, Form, Switch, Row, Col, Typography, Table, Modal, Popconfirm } from 'antd';
import { SaveOutlined, ApiOutlined, SendOutlined, KeyOutlined, CopyOutlined, ReloadOutlined, PlusOutlined, DeleteOutlined, SafetyCertificateOutlined, UserOutlined } from '@ant-design/icons';
import {
    getTelegramConfig, setTelegramConfig, testTelegramPush,
    getDeepSeekConfig, setDeepSeekConfig, testDeepSeekConnection,
    getAnalystApiKeys, createAnalystApiKey, deleteAnalystApiKey,
    getSystemTimezone, setSystemTimezone,
    getDailyPushTime, setDailyPushTime,
    getAutoPipelineConfig, setAutoPipelineConfig,
    updateCredentials,
    getTimeWindowsConfig, setTimeWindowsConfig
} from '../../api';
import { GlobalOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import customParseFormat from 'dayjs/plugin/customParseFormat';
dayjs.extend(customParseFormat);

import { TimePicker } from 'antd';
import TimeRangeSelect from './TimeRangeSelect';

const { Option } = Select;
const { Text, Paragraph } = Typography;

const ApiSettingsTab = () => {
    // DeepSeek 配置状态
    const [deepseekConfig, setDeepSeekConfigState] = useState({ api_key: '', base_url: 'https://api.deepseek.com', model: 'deepseek-chat' });

    // Telegram 配置状态
    const [telegramConfig, setTelegramConfigState] = useState({ bot_token: '', chat_id: '', enabled: false });

    // 分析师API密钥状态（多密钥）
    const [apiKeys, setApiKeys] = useState([]);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [newKeyName, setNewKeyName] = useState('');
    const [newKeyNotes, setNewKeyNotes] = useState('');

    // System Config State
    const [timezone, setTimezone] = useState('Asia/Shanghai');
    const [pushTime, setPushTime] = useState('20:00');
    const [articlePushTime, setArticlePushTime] = useState('21:00');
    const [loadingTz, setLoadingTz] = useState(false);

    // Auto-Pipeline Config State (News)
    const [dedupHours, setDedupHours] = useState(2);
    const [dedupWindowHours, setDedupWindowHours] = useState(2); // 快讯去重时间窗口
    const [filterHours, setFilterHours] = useState(24);
    const [aiScoringHours, setAiScoringHours] = useState(10);
    const [pushHours, setPushHours] = useState(2);

    // Auto-Pipeline Config State (Articles)
    const [articleDedupHours, setArticleDedupHours] = useState(2);
    const [articleDedupWindowHours, setArticleDedupWindowHours] = useState(72); // 文章去重时间窗口：3天=72小时
    const [articleFilterHours, setArticleFilterHours] = useState(24);
    const [articleAiScoringHours, setArticleAiScoringHours] = useState(10);
    const [articlePushHours, setArticlePushHours] = useState(2);

    // Credential Update State
    const [credentialForm] = Form.useForm();
    const [credentialLoading, setCredentialLoading] = useState(false);

    useEffect(() => {
        fetchDeepSeekConfig();
        fetchTelegramConfig();
        fetchAnalystApiKeys();
        fetchTimezone();
        fetchPushTime();
        fetchAutoPipelineConfig();
        fetchTimeWindowsConfig();
    }, []);

    const fetchTimezone = async () => {
        try {
            const res = await getSystemTimezone();
            if (res.data && res.data.timezone) {
                setTimezone(res.data.timezone);
            }
        } catch (error) {
            console.error("Failed to fetch timezone", error);
        }
    };

    const fetchTimeWindowsConfig = async () => {
        try {
            const res = await getTimeWindowsConfig();
            if (res.data) {
                // Load article config
                if (res.data.article) {
                    setArticleDedupHours(res.data.article.dedup_hours || 168);
                    setArticleDedupWindowHours(res.data.article.dedup_window_hours || 72);
                    setArticleFilterHours(res.data.article.filter_hours || 168);
                    setArticleAiScoringHours(res.data.article.ai_scoring_hours || 168);
                    setArticlePushHours(res.data.article.push_hours || 72);
                }
                // Load news config
                if (res.data.news) {
                    setDedupHours(res.data.news.dedup_hours || 2);
                    setDedupWindowHours(res.data.news.dedup_window_hours || 2);
                    setFilterHours(res.data.news.filter_hours || 24);
                }
            }
        } catch (error) {
            console.error("Failed to fetch time windows config", error);
        }
    };

    const fetchPushTime = async () => {
        try {
            const res = await getDailyPushTime();
            if (res.data) {
                if (res.data.time) {
                    setPushTime(res.data.time);
                }
                if (res.data.article_time) {
                    setArticlePushTime(res.data.article_time);
                }
            }
        } catch (error) {
            console.error("Failed to fetch push time", error);
        }
    };

    const fetchAutoPipelineConfig = async () => {
        try {
            const res = await getAutoPipelineConfig();
            if (res.data) {
                // News config
                setDedupHours(res.data.dedup_hours || 2);
                setFilterHours(res.data.filter_hours || 24);
                setAiScoringHours(res.data.ai_scoring_hours || 10);
                setPushHours(res.data.push_hours || 2);

                // Article config
                setArticleDedupHours(res.data.article_dedup_hours || 2);
                setArticleFilterHours(res.data.article_filter_hours || 24);
                setArticleAiScoringHours(res.data.article_ai_scoring_hours || 10);
                setArticlePushHours(res.data.article_push_hours || 2);
            }
        } catch (error) {
            console.error("Failed to fetch auto-pipeline config", error);
        }
    };

    const handleSaveTimezone = async () => {
        setLoadingTz(true);
        try {
            // Save timezone
            await setSystemTimezone({ timezone });
            // Save push time (both news and articles)
            await setDailyPushTime({ time: pushTime, article_time: articlePushTime });

            // Save time windows config (new API)
            await setTimeWindowsConfig({
                article: {
                    dedup_hours: articleDedupHours,
                    dedup_window_hours: articleDedupWindowHours,
                    filter_hours: articleFilterHours,
                    ai_scoring_hours: articleAiScoringHours,
                    push_hours: articlePushHours
                },
                news: {
                    dedup_hours: dedupHours,
                    dedup_window_hours: dedupWindowHours,
                    filter_hours: filterHours
                }
            });

            // Save auto-pipeline config (for compatibility, excluding time windows which are saved above)
            await setAutoPipelineConfig({
                ai_scoring_hours: aiScoringHours,
                push_hours: pushHours
            });

            message.success("系统配置已更新");
        } catch (error) {
            message.error("保存失败: " + (error.response?.data?.detail || error.message));
        } finally {
            setLoadingTz(false);
        }
    };

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

    const fetchAnalystApiKeys = async () => {
        try {
            const res = await getAnalystApiKeys();
            setApiKeys(res.data || []);
        } catch (error) {
            console.error("Failed to fetch analyst API keys", error);
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

    // 分析师API Handlers
    const handleCreateApiKey = async () => {
        if (!newKeyName.trim()) {
            message.warning('请输入密钥名称');
            return;
        }

        try {
            const res = await createAnalystApiKey(newKeyName, newKeyNotes);
            message.success(res.message || '密钥创建成功');
            setShowCreateModal(false);
            setNewKeyName('');
            setNewKeyNotes('');
            fetchAnalystApiKeys(); // 刷新列表
        } catch (error) {
            message.error('创建失败: ' + (error.response?.data?.detail || error.message));
        }
    };

    const handleDeleteApiKey = async (keyId, keyName) => {
        try {
            await deleteAnalystApiKey(keyId);
            message.success(`密钥 "${keyName}" 已删除`);
            fetchAnalystApiKeys(); // 刷新列表
        } catch (error) {
            message.error('删除失败: ' + (error.response?.data?.detail || error.message));
        }
    };

    const handleCopyApiKey = (apiKey) => {
        navigator.clipboard.writeText(apiKey);
        message.success('密钥已复制到剪贴板');
    };

    const handleUpdateCredentials = async (values) => {
        try {
            setCredentialLoading(true);
            await updateCredentials({
                current_password: values.current_password,
                new_username: values.new_username,
                new_password: values.new_password
            });
            message.success("账户信息更新成功！请重新登录。");
            credentialForm.resetFields();
            // 可以在此强制退出
            localStorage.removeItem('token');
            window.location.href = '/login';
        } catch (error) {
            message.error("更新失败: " + (error.response?.data?.detail || error.message));
        } finally {
            setCredentialLoading(false);
        }
    };

    // Table列定义
    const apiKeyColumns = [
        {
            title: '名称',
            dataIndex: 'key_name',
            key: 'key_name',
            width: 150,
        },
        {
            title: 'API密钥',
            dataIndex: 'api_key',
            key: 'api_key',
            render: (text) => (
                <Input.Password
                    value={text}
                    readOnly
                    style={{ width: 300 }}
                    suffix={
                        <CopyOutlined
                            onClick={() => handleCopyApiKey(text)}
                            style={{ cursor: 'pointer', color: '#1890ff' }}
                        />
                    }
                />
            ),
        },
        {
            title: '创建时间',
            dataIndex: 'created_at',
            key: 'created_at',
            width: 160,
        },
        {
            title: '最后使用',
            dataIndex: 'last_used_at',
            key: 'last_used_at',
            width: 160,
            render: (text) => text || '未使用',
        },
        {
            title: '操作',
            key: 'action',
            width: 120,
            render: (_, record) => (
                <Space>
                    <Button
                        size="small"
                        icon={<CopyOutlined />}
                        onClick={() => handleCopyApiKey(record.api_key)}
                    >
                        复制
                    </Button>
                    <Popconfirm
                        title="确定删除此密钥？"
                        description={`删除后使用此密钥的用户将无法访问API`}
                        onConfirm={() => handleDeleteApiKey(record.id, record.key_name)}
                        okText="确认"
                        cancelText="取消"
                    >
                        <Button size="small" danger icon={<DeleteOutlined />}>
                            删除
                        </Button>
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    return (
        <div style={{ padding: '0 10px' }}>
            <h3>全局 API 配置</h3>

            {/* System Configuration */}
            <Row gutter={16} style={{ marginBottom: 20 }}>
                <Col xs={24}>
                    <Card title={<Space><GlobalOutlined /> 系统基础配置</Space>}>
                        <Form layout="inline" style={{ flexWrap: 'wrap' }}>
                            <Form.Item label="系统时区 (System Timezone)" style={{ marginBottom: 16, minWidth: 300 }}>
                                <Select
                                    value={timezone}
                                    onChange={setTimezone}
                                    style={{ width: 250 }}
                                    showSearch
                                >
                                    <Option value="Asia/Shanghai">Asia/Shanghai (北京时间)</Option>
                                    <Option value="UTC">UTC (世界协调时)</Option>
                                    <Option value="America/New_York">America/New_York (美东)</Option>
                                    <Option value="America/Los_Angeles">America/Los_Angeles (美西)</Option>
                                    <Option value="Europe/London">Europe/London (伦敦)</Option>
                                    <Option value="Asia/Tokyo">Asia/Tokyo (东京)</Option>
                                    <Option value="Asia/Singapore">Asia/Singapore (新加坡)</Option>
                                    <Option value="Australia/Sydney">Australia/Sydney (悉尼)</Option>
                                </Select>
                            </Form.Item>

                            {/* 自动化流程配置 - 单独一行 */}
                            <div style={{ width: '100%', marginBottom: 16 }} />

                            <div style={{ width: '100%', marginBottom: 8 }}>
                                <Text strong>快讯（News）配置：</Text>
                            </div>

                            <Form.Item label="去重时间窗口" style={{ marginBottom: 16 }}>
                                <TimeRangeSelect value={dedupWindowHours} onChange={setDedupWindowHours} />
                            </Form.Item>

                            <Form.Item label="去重时间范围" style={{ marginBottom: 16 }}>
                                <TimeRangeSelect value={dedupHours} onChange={setDedupHours} />
                            </Form.Item>

                            <Form.Item label="过滤时间范围" style={{ marginBottom: 16 }}>
                                <TimeRangeSelect value={filterHours} onChange={setFilterHours} />
                            </Form.Item>

                            <Form.Item label="AI打分时间范围" style={{ marginBottom: 16 }}>
                                <TimeRangeSelect value={aiScoringHours} onChange={setAiScoringHours} />
                            </Form.Item>

                            <Form.Item label="推送时间范围" style={{ marginBottom: 16 }}>
                                <TimeRangeSelect value={pushHours} onChange={setPushHours} />
                            </Form.Item>

                            <Form.Item label="每日新闻日报推送时间" style={{ marginBottom: 16 }}>
                                <Input
                                    type="time"
                                    value={pushTime}
                                    onChange={(e) => setPushTime(e.target.value)}
                                    style={{ width: 120 }}
                                />
                            </Form.Item>

                            <div style={{ width: '100%', marginBottom: 8, marginTop: 16 }}>
                                <Text strong>深度文章（Articles）配置：</Text>
                            </div>

                            <Form.Item label="去重时间窗口" style={{ marginBottom: 16 }}>
                                <TimeRangeSelect value={articleDedupWindowHours} onChange={setArticleDedupWindowHours} />
                            </Form.Item>

                            <Form.Item label="去重时间范围" style={{ marginBottom: 16 }}>
                                <TimeRangeSelect value={articleDedupHours} onChange={setArticleDedupHours} />
                            </Form.Item>

                            <Form.Item label="过滤时间范围" style={{ marginBottom: 16 }}>
                                <TimeRangeSelect value={articleFilterHours} onChange={setArticleFilterHours} />
                            </Form.Item>

                            <Form.Item label="AI打分时间范围" style={{ marginBottom: 16 }}>
                                <TimeRangeSelect value={articleAiScoringHours} onChange={setArticleAiScoringHours} />
                            </Form.Item>

                            <Form.Item label="推送时间范围" style={{ marginBottom: 16 }}>
                                <TimeRangeSelect value={articlePushHours} onChange={setArticlePushHours} />
                            </Form.Item>

                            <Form.Item label="每日文章日报推送时间" style={{ marginBottom: 16 }}>
                                <Input
                                    type="time"
                                    value={articlePushTime}
                                    onChange={(e) => setArticlePushTime(e.target.value)}
                                    style={{ width: 120 }}
                                />
                            </Form.Item>

                            <div style={{ width: '100%', marginTop: 16 }}>
                                <Button
                                    type="primary"
                                    icon={<SaveOutlined />}
                                    onClick={handleSaveTimezone}
                                    loading={loadingTz}
                                >
                                    保存设置
                                </Button>
                            </div>

                            <div style={{ marginTop: 8, color: '#666', fontSize: 13, width: '100%' }}>
                                * 此设置将影响所有定时任务（如工作时间判断、每日推送、数据去重范围等）。修改后立即生效。
                            </div>
                        </Form>
                    </Card>
                </Col>
            </Row>

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



            {/* Account Security and Analyst API (Side by Side) */}
            <Row gutter={16} style={{ marginBottom: 20 }}>
                <Col xs={24} lg={12}>
                    <Card title={<Space><SafetyCertificateOutlined /> 账户安全设置 (Account Security)</Space>} style={{ height: '100%' }}>
                        <Form
                            layout="vertical"
                            form={credentialForm}
                            onFinish={handleUpdateCredentials}
                        >
                            <Form.Item
                                label="当前密码 (Verify Current Password)"
                                name="current_password"
                                rules={[{ required: true, message: '请输入当前密码以验证身份' }]}
                            >
                                <Input.Password
                                    placeholder="验证您的当前密码"
                                    autoComplete="current-password"
                                />
                            </Form.Item>

                            {/* 隐藏的username input，用于辅助浏览器正确识别表单类型 */}
                            <Input name="username" style={{ display: 'none' }} autoComplete="username" />

                            <Form.Item
                                label="新用户名 (New Username)"
                                name="new_username"
                                tooltip="留空则不修改。修改后需使用新用户名登录。"
                            >
                                <Input
                                    prefix={<UserOutlined />}
                                    placeholder="不修改请留空"
                                    autoComplete="off"
                                />
                            </Form.Item>

                            <Form.Item
                                label="新密码 (New Password)"
                                name="new_password"
                                rules={[
                                    { min: 6, message: '密码长度至少6位' }
                                ]}
                                tooltip="留空则不修改。修改后需使用新密码登录。"
                            >
                                <Input.Password
                                    placeholder="不修改请留空"
                                    autoComplete="new-password"
                                />
                            </Form.Item>

                            <Form.Item
                                label="确认新密码 (Confirm New Password)"
                                name="confirm_password"
                                dependencies={['new_password']}
                                rules={[
                                    ({ getFieldValue }) => ({
                                        validator(_, value) {
                                            if (!value || getFieldValue('new_password') === value) {
                                                return Promise.resolve();
                                            }
                                            return Promise.reject(new Error('两次输入的密码不一致!'));
                                        },
                                    }),
                                ]}
                            >
                                <Input.Password
                                    placeholder="再次输入新密码"
                                    autoComplete="new-password"
                                />
                            </Form.Item>

                            <Form.Item>
                                <Button type="primary" htmlType="submit" loading={credentialLoading} danger block>
                                    更新账户信息
                                </Button>
                            </Form.Item>
                        </Form>
                    </Card>
                </Col>

                <Col xs={24} lg={12}>
                    <Card
                        title={<Space><KeyOutlined /> 分析师API密钥管理</Space>}
                        style={{ height: '100%' }}
                        extra={
                            <Button
                                type="primary"
                                icon={<PlusOutlined />}
                                onClick={() => setShowCreateModal(true)}
                                size="small"
                            >
                                新建
                            </Button>
                        }
                    >
                        <Table
                            dataSource={apiKeys}
                            columns={apiKeyColumns}
                            rowKey="id"
                            pagination={false}
                            locale={{ emptyText: '暂无密钥' }}
                            scroll={{ x: true }}
                            size="small"
                        />
                        <div style={{ marginTop: 16, background: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
                            <Text strong>使用说明：</Text>
                            <ul style={{ marginTop: 8, marginBottom: 0, paddingLeft: 20 }}>
                                <li>为不同用户生成独立密钥</li>
                                <li>密钥可独立删除</li>
                                <li><code>GET /api/analyst/news</code></li>
                            </ul>
                        </div>
                    </Card>
                </Col>
            </Row>

            {/* 创建密钥Modal */}
            <Modal
                title="创建新API密钥"
                open={showCreateModal}
                onOk={handleCreateApiKey}
                onCancel={() => {
                    setShowCreateModal(false);
                    setNewKeyName('');
                    setNewKeyNotes('');
                }}
                okText="创建"
                cancelText="取消"
            >
                <Form layout="vertical">
                    <Form.Item
                        label="密钥名称"
                        required
                        extra="用于标识此密钥的用途或使用者"
                    >
                        <Input
                            value={newKeyName}
                            onChange={(e) => setNewKeyName(e.target.value)}
                            placeholder="请输入密钥名称"
                        />
                    </Form.Item>
                    <Form.Item label="备注（可选）">
                        <Input.TextArea
                            value={newKeyNotes}
                            onChange={(e) => setNewKeyNotes(e.target.value)}
                            placeholder="备注信息"
                            rows={3}
                        />
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
};

export default ApiSettingsTab;
