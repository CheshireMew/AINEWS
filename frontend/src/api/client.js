/**
 * API客户端 - 统一处理API请求和响应
 */

import { message } from 'antd';

class APIClient {
    /**
     * 通用请求方法
     * @param {string} url - 请求URL
     * @param {Object} options - fetch选项
     * @returns {Promise<Object>} - 响应数据
     */
    async request(url, options = {}) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
            });

            const data = await response.json();

            // 检查响应是否成功
            if (!data.success) {
                // 显示错误消息
                message.error(data.message || '请求失败');
                throw new Error(data.message || '请求失败');
            }

            return data;
        } catch (error) {
            // 网络错误或其他错误
            if (!error.message.includes('请求失败')) {
                message.error('网络错误，请稍后重试');
            }
            throw error;
        }
    }

    /**
     * GET请求
     * @param {string} url - 请求URL
     * @param {Object} params - URL参数
     * @returns {Promise<Object>}
     */
    async get(url, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        return this.request(fullUrl);
    }

    /**
     * POST请求
     * @param {string} url - 请求URL
     * @param {Object} body - 请求体
     * @returns {Promise<Object>}
     */
    async post(url, body) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(body),
        });
    }

    /**
     * PUT请求
     * @param {string} url - 请求URL
     * @param {Object} body - 请求体
     * @returns {Promise<Object>}
     */
    async put(url, body) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(body),
        });
    }

    /**
     * DELETE请求
     * @param {string} url - 请求URL
     * @returns {Promise<Object>}
     */
    async delete(url) {
        return this.request(url, {
            method: 'DELETE',
        });
    }
}

// 导出单例
export default new APIClient();
