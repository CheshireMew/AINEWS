import React from 'react';
import PropTypes from 'prop-types';

/**
 * 通用分页配置组件
 * 用于所有表格的分页设置
 */
const usePaginationConfig = (defaultPageSize = 10) => {
    /**
     * 创建antd Table的pagination配置
     * @param {Object} pagination - 分页状态 {current, pageSize, total}
     * @param {Function} onPageChange - 页码变化回调
     * @param {Function} onPageSizeChange - 每页数量变化回调
     */
    const getPaginationConfig = (pagination, onPageChange, onPageSizeChange) => {
        return {
            current: pagination.current,
            pageSize: pagination.pageSize || defaultPageSize,
            total: pagination.total,
            showSizeChanger: true,

            showTotal: (total) => `共 ${total} 条`,
            pageSizeOptions: ['10', '20', '50', '100'],
            onChange: (page, pageSize) => {
                // 页码变化
                if (onPageChange) {
                    onPageChange(page, pageSize);
                }
            },
            onShowSizeChange: (current, size) => {
                // 每页数量变化，重置到第1页
                if (onPageSizeChange) {
                    onPageSizeChange(1, size);
                }
            }
        };
    };

    return { getPaginationConfig };
};

usePaginationConfig.propTypes = {
    defaultPageSize: PropTypes.number
};

export default usePaginationConfig;
