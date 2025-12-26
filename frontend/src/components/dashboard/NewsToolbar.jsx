import React from 'react';
import { Button, Input, Select, Space } from 'antd';
import { SearchOutlined, DownloadOutlined, ReloadOutlined } from '@ant-design/icons';

const { Option } = Select;
// const { Search } = Input; // remove Search since we use Input now

/**
 * 通用新闻工具栏组件
 * 提供搜索、来源筛选、导出、刷新等标准功能，并支持扩展
 */
const NewsToolbar = ({
    onSearch,           // 搜索回调 (value) => {}
    searchPlaceholder = "搜索新闻...",

    spiders,            // 爬虫列表 (用于来源筛选)
    selectedSource,     // 当前选中的来源
    onSourceChange,     // 来源变更回调 (value) => {}

    onExport,           // 导出回调 () => {}

    onRefresh,          // 刷新回调 () => {}
    loading,            // 加载状态

    children,           // 额外操作按钮 (如手动去重、时间筛选等)
    style               // 自定义样式
}) => {
    // 防抖处理搜索
    const handleSearchChange = (e) => {
        const value = e.target.value;
        if (onSearch) {
            // 清除之前的定时器
            if (window.searchTimeout) clearTimeout(window.searchTimeout);
            // 设置新的定时器 (500ms防抖)
            window.searchTimeout = setTimeout(() => {
                onSearch(value);
            }, 500);
        }
    };

    return (
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8, ...style }}>
            <Space size={12} wrap align="center">
                {/* 1. 搜索框 */}
                {onSearch && (
                    <Input
                        placeholder={searchPlaceholder}
                        allowClear
                        prefix={<SearchOutlined style={{ color: 'rgba(0,0,0,0.25)' }} />}
                        onChange={handleSearchChange}
                        style={{ width: 300 }}
                    />
                )}

                {/* 2. 来源筛选 */}
                {spiders && onSourceChange && (
                    <Space size={4}>
                        <span style={{ fontSize: 14 }}>来源:</span>
                        <Select
                            value={selectedSource}
                            style={{ width: 160 }}
                            onChange={onSourceChange}
                        >
                            <Option value="">全部来源</Option>
                            {spiders.map(s => <Option key={s} value={s}>{s}</Option>)}
                        </Select>
                    </Space>
                )}

                {/* 3. 导出按钮 */}
                {onExport && (
                    <Button icon={<DownloadOutlined />} onClick={onExport}>导出</Button>
                )}

                {/* 4. 额外操作 (插槽) */}
                {children}
            </Space>

            {/* 5. 刷新按钮 (靠右) */}
            <Space>
                {onRefresh && (
                    <Button icon={<ReloadOutlined />} onClick={onRefresh} loading={loading}>刷新</Button>
                )}
            </Space>
        </div>
    );
};

export default NewsToolbar;
