import { useState } from 'react';

/**
 * 通用分页Hook
 * @param {Function} fetchFn - 数据获取函数，接收(page, limit, ...params)
 * @returns {Object} - { data, loading, pagination, handlePageChange, refresh }
 */
export const usePagination = (fetchFn) => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [pagination, setPagination] = useState({
        current: 1,
        pageSize: 20,
        total: 0
    });

    /**
     * 加载数据
     * @param {number} page - 页码
     * @param {number} pageSize - 每页数量
     * @param {...any} params - 额外参数
     */
    const loadData = async (page, pageSize, ...params) => {
        setLoading(true);
        try {
            const result = await fetchFn(page, pageSize, ...params);
            setData(result.data || []);
            setPagination({
                current: result.page || page,
                pageSize: result.limit || pageSize,
                total: result.total || 0
            });
        } catch (error) {
            console.error('Failed to load data:', error);
            setData([]);
        } finally {
            setLoading(false);
        }
    };

    /**
     * 处理分页变化
     */
    const handlePageChange = (page, pageSize) => {
        loadData(page, pageSize);
    };

    /**
     * 刷新当前页
     */
    const refresh = () => {
        loadData(pagination.current, pagination.pageSize);
    };

    return {
        data,
        loading,
        pagination,
        handlePageChange,
        refresh,
        loadData
    };
};
