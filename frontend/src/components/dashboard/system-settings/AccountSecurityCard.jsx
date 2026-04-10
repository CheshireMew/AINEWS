import React from 'react';
import { Button, Card, Form, Input, Space } from 'antd';
import { SafetyCertificateOutlined, UserOutlined } from '@ant-design/icons';
import { useAccountSecurity } from '../../../hooks/dashboard/system-settings/useAccountSecurity';

export default function AccountSecurityCard() {
    const [form] = Form.useForm();
    const { loading, submit } = useAccountSecurity(form);

    return (
        <Card title={<Space><SafetyCertificateOutlined /> 账户安全设置</Space>} style={{ height: '100%' }}>
            <Form layout="vertical" form={form} onFinish={submit}>
                <Form.Item label="当前密码" name="current_password" rules={[{ required: true, message: '请输入当前密码以验证身份' }]}>
                    <Input.Password placeholder="验证当前密码" autoComplete="current-password" />
                </Form.Item>
                <Input name="username" style={{ display: 'none' }} autoComplete="username" />
                <Form.Item label="新用户名" name="new_username" tooltip="留空则不修改">
                    <Input prefix={<UserOutlined />} placeholder="不修改请留空" autoComplete="off" />
                </Form.Item>
                <Form.Item label="新密码" name="new_password" rules={[{ min: 6, message: '密码长度至少6位' }]} tooltip="留空则不修改">
                    <Input.Password placeholder="不修改请留空" autoComplete="new-password" />
                </Form.Item>
                <Form.Item
                    label="确认新密码"
                    name="confirm_password"
                    dependencies={['new_password']}
                    rules={[
                        ({ getFieldValue }) => ({
                            validator(_, value) {
                                if (!value || getFieldValue('new_password') === value) {
                                    return Promise.resolve();
                                }
                                return Promise.reject(new Error('两次输入的密码不一致'));
                            },
                        }),
                    ]}
                >
                    <Input.Password placeholder="再次输入新密码" autoComplete="new-password" />
                </Form.Item>
                <Form.Item>
                    <Button type="primary" htmlType="submit" loading={loading} danger block>
                        更新账户信息
                    </Button>
                </Form.Item>
            </Form>
        </Card>
    );
}
