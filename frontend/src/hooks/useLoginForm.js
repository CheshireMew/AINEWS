import { useState } from 'react';
import { message } from 'antd';

import { login } from '../api/auth';
import { getRequestErrorMessage } from './dashboard/listStateHelpers';

export function useLoginForm(navigate) {
    const [loading, setLoading] = useState(false);

    const submit = async (values) => {
        setLoading(true);
        try {
            await login(values.username, values.password);
            message.success('登录成功');
            navigate('/admin');
        } catch (error) {
            message.error(`登录失败: ${getRequestErrorMessage(error, '请检查管理员账号配置')}`);
        } finally {
            setLoading(false);
        }
    };

    return { loading, submit };
}
