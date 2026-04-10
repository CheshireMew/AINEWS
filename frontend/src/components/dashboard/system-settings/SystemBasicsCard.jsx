import React from 'react';
import { Button, Card, Form, Input, Select, Space, Typography } from 'antd';
import { GlobalOutlined, SaveOutlined } from '@ant-design/icons';
import { useSystemBasicsSettings } from '../../../hooks/dashboard/system-settings/useSystemBasicsSettings';
import TimeRangeSelect from '../TimeRangeSelect';

const { Option } = Select;
const { Text } = Typography;

export default function SystemBasicsCard() {
    const { timezone, loading, newsConfig, articleConfig, deliverySchedule, setTimezone, setDeliverySchedule, updateHours, save } = useSystemBasicsSettings();

    return (
        <Card title={<Space><GlobalOutlined /> 系统基础配置</Space>}>
            <Form layout="inline" style={{ flexWrap: 'wrap' }}>
                <Form.Item label="系统时区" style={{ marginBottom: 16, minWidth: 300 }}>
                    <Select value={timezone} onChange={setTimezone} style={{ width: 250 }} showSearch>
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

                <div style={{ width: '100%', marginBottom: 16 }} />
                <div style={{ width: '100%', marginBottom: 8 }}>
                    <Text strong>快讯配置</Text>
                </div>
                <Form.Item label="去重时间窗口" style={{ marginBottom: 16 }}>
                    <TimeRangeSelect value={newsConfig.dedup_window_hours} onChange={(value) => updateHours('news', 'dedup_window_hours', value)} />
                </Form.Item>
                <Form.Item label="去重时间范围" style={{ marginBottom: 16 }}>
                    <TimeRangeSelect value={newsConfig.dedup_hours} onChange={(value) => updateHours('news', 'dedup_hours', value)} />
                </Form.Item>
                <Form.Item label="过滤时间范围" style={{ marginBottom: 16 }}>
                    <TimeRangeSelect value={newsConfig.filter_hours} onChange={(value) => updateHours('news', 'filter_hours', value)} />
                </Form.Item>
                <Form.Item label="AI打分时间范围" style={{ marginBottom: 16 }}>
                    <TimeRangeSelect value={newsConfig.ai_scoring_hours} onChange={(value) => updateHours('news', 'ai_scoring_hours', value)} />
                </Form.Item>
                <Form.Item label="推送时间范围" style={{ marginBottom: 16 }}>
                    <TimeRangeSelect value={newsConfig.push_hours} onChange={(value) => updateHours('news', 'push_hours', value)} />
                </Form.Item>

                <div style={{ width: '100%', marginBottom: 8, marginTop: 16 }}>
                    <Text strong>深度文章配置</Text>
                </div>
                <Form.Item label="去重时间窗口" style={{ marginBottom: 16 }}>
                    <TimeRangeSelect value={articleConfig.dedup_window_hours} onChange={(value) => updateHours('article', 'dedup_window_hours', value)} />
                </Form.Item>
                <Form.Item label="去重时间范围" style={{ marginBottom: 16 }}>
                    <TimeRangeSelect value={articleConfig.dedup_hours} onChange={(value) => updateHours('article', 'dedup_hours', value)} />
                </Form.Item>
                <Form.Item label="过滤时间范围" style={{ marginBottom: 16 }}>
                    <TimeRangeSelect value={articleConfig.filter_hours} onChange={(value) => updateHours('article', 'filter_hours', value)} />
                </Form.Item>
                <Form.Item label="AI打分时间范围" style={{ marginBottom: 16 }}>
                    <TimeRangeSelect value={articleConfig.ai_scoring_hours} onChange={(value) => updateHours('article', 'ai_scoring_hours', value)} />
                </Form.Item>
                <Form.Item label="推送时间范围" style={{ marginBottom: 16 }}>
                    <TimeRangeSelect value={articleConfig.push_hours} onChange={(value) => updateHours('article', 'push_hours', value)} />
                </Form.Item>

                <div style={{ width: '100%', marginBottom: 8, marginTop: 16 }}>
                    <Text strong>日报推送时间</Text>
                </div>
                <Form.Item label="快讯日报" style={{ marginBottom: 16 }}>
                    <Input
                        value={deliverySchedule.news_time}
                        onChange={(event) => setDeliverySchedule((prev) => ({ ...prev, news_time: event.target.value }))}
                        style={{ width: 120 }}
                        placeholder="20:00"
                    />
                </Form.Item>
                <Form.Item label="文章日报" style={{ marginBottom: 16 }}>
                    <Input
                        value={deliverySchedule.article_time}
                        onChange={(event) => setDeliverySchedule((prev) => ({ ...prev, article_time: event.target.value }))}
                        style={{ width: 120 }}
                        placeholder="21:00"
                    />
                </Form.Item>

                <div style={{ width: '100%', marginTop: 16 }}>
                    <Button type="primary" icon={<SaveOutlined />} onClick={save} loading={loading}>
                        保存设置
                    </Button>
                </div>
                <div style={{ marginTop: 8, color: '#666', fontSize: 13, width: '100%' }}>
                    * 此设置会影响定时任务、数据处理窗口和日报投递时间。
                </div>
            </Form>
        </Card>
    );
}
