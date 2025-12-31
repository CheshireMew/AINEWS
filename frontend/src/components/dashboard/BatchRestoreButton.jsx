import React from 'react';
import PropTypes from 'prop-types';
import { Button, message, Popconfirm } from 'antd';
import { batchRestoreDeduplicated } from '../../api';

/**
 * 批量还原按钮组件
 * 独立封装，避免受其他功能修改影响
 */
const BatchRestoreButton = ({ onSuccess, contentType }) => {

    const handleBatchRestore = async () => {
        try {
            const res = await batchRestoreDeduplicated(contentType);
            message.success({
                content: `批量还原成功！还原了 ${res.data.restored_count} 条数据。请切换到"重复对照"Tab刷新查看。`,
                duration: 5
            });

            if (onSuccess) {
                onSuccess();
            }

            // 触发页面刷新提示
            setTimeout(() => {
                message.info('建议刷新页面（F5）以查看最新数据', 3);
            }, 2000);
        } catch (e) {
            message.error('批量还原失败: ' + (e.response?.data?.detail || e.message));
        }
    };

    return (
        <Popconfirm
            title="还原已去重数据"
            description="确定要还原已处理的去重数据吗？这将把数据还原到 news 表的 'raw' 状态。（注：已进行AI筛选或推送的新闻将被自动保留，不会被清除）"
            onConfirm={handleBatchRestore}
            okText="确定"
            cancelText="取消"
        >
            <Button type="primary" danger>
                还原已去重数据
            </Button>
        </Popconfirm>
    );
};

BatchRestoreButton.propTypes = {
    onSuccess: PropTypes.func,
    contentType: PropTypes.string
};

export default BatchRestoreButton;
