import { useCallback, useState } from 'react';

export const createPaginationConfig = (pagination, onPageChange, defaultPageSize = 10) => ({
    current: pagination.current,
    pageSize: pagination.pageSize || defaultPageSize,
    total: pagination.total,
    showSizeChanger: true,
    showTotal: (total) => `共 ${total} 条`,
    pageSizeOptions: ['10', '20', '50', '100'],
    onChange: (page, pageSize) => {
        if (onPageChange) {
            onPageChange(page, pageSize);
        }
    },
    onShowSizeChange: (_, size) => {
        if (onPageChange) {
            onPageChange(1, size);
        }
    }
});

export const usePagination = (fetchFn) => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [pagination, setPagination] = useState({
        current: 1,
        pageSize: 20,
        total: 0
    });

    const loadData = useCallback(async (page, pageSize, ...params) => {
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
    }, [fetchFn]);

    const handlePageChange = useCallback((page, pageSize) => {
        loadData(page, pageSize);
    }, [loadData]);

    const refresh = useCallback(() => {
        loadData(pagination.current, pagination.pageSize);
    }, [loadData, pagination]);

    return {
        data,
        loading,
        pagination,
        handlePageChange,
        refresh,
        loadData,
        getPaginationConfig: (defaultPageSize = pagination.pageSize || 10, onPageChange = handlePageChange) => (
            createPaginationConfig(pagination, onPageChange, defaultPageSize)
        )
    };
};
