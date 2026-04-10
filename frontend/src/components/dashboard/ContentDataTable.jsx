import React from 'react';
import PropTypes from 'prop-types';
import { Table } from 'antd';

import { createPaginationConfig } from '../../hooks/usePagination';
import NewsExpandedView from './NewsExpandedView';
import NewsToolbar from './NewsToolbar';

export default function ContentDataTable({
    listState,
    columns,
    spiders,
    contentKind,
    exportScope,
    onShowExport,
    toolbarChildren,
    showSourceFilter = true,
    searchPlaceholder,
    size,
    wrapperStyle,
}) {
    const {
        items,
        loading,
        pagination,
        filterSource,
        filterKeyword,
        setFilterSource,
        setFilterKeyword,
        fetchItems,
    } = listState;

    const currentSource = showSourceFilter ? filterSource : undefined;

    const handleSearch = (value) => {
        setFilterKeyword(value);
        fetchItems(1, pagination.pageSize, currentSource, value);
    };

    const handleSourceChange = showSourceFilter && setFilterSource
        ? (value) => {
            const nextSource = value || undefined;
            setFilterSource(nextSource);
            fetchItems(1, pagination.pageSize, nextSource, filterKeyword);
        }
        : undefined;

    const handleRefresh = () => {
        fetchItems(pagination.current, pagination.pageSize, currentSource, filterKeyword);
    };

    const handlePageChange = (page, pageSize) => {
        fetchItems(page, pageSize, currentSource, filterKeyword);
    };

    return (
        <div style={wrapperStyle}>
            <NewsToolbar
                onSearch={handleSearch}
                searchPlaceholder={searchPlaceholder}
                spiders={showSourceFilter ? spiders : undefined}
                selectedSource={currentSource}
                onSourceChange={handleSourceChange}
                contentKind={contentKind}
                onExport={exportScope && onShowExport ? () => onShowExport(exportScope) : undefined}
                onRefresh={handleRefresh}
                loading={loading}
            >
                {toolbarChildren}
            </NewsToolbar>

            <Table
                columns={columns}
                dataSource={items}
                rowKey="id"
                loading={loading}
                pagination={createPaginationConfig(pagination, handlePageChange)}
                size={size}
                expandable={{
                    expandedRowRender: (record) => <NewsExpandedView record={record} />,
                    rowExpandable: () => true,
                }}
            />
        </div>
    );
}

ContentDataTable.propTypes = {
    listState: PropTypes.shape({
        items: PropTypes.array,
        loading: PropTypes.bool,
        pagination: PropTypes.object,
        filterSource: PropTypes.string,
        filterKeyword: PropTypes.string,
        setFilterSource: PropTypes.func,
        setFilterKeyword: PropTypes.func,
        fetchItems: PropTypes.func,
    }).isRequired,
    columns: PropTypes.arrayOf(PropTypes.object).isRequired,
    spiders: PropTypes.arrayOf(PropTypes.object),
    contentKind: PropTypes.string,
    exportScope: PropTypes.string,
    onShowExport: PropTypes.func,
    toolbarChildren: PropTypes.node,
    showSourceFilter: PropTypes.bool,
    searchPlaceholder: PropTypes.string,
    size: PropTypes.string,
    wrapperStyle: PropTypes.object,
};
