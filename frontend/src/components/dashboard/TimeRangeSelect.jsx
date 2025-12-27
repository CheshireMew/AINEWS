import React from 'react';
import PropTypes from 'prop-types';
import { Select } from 'antd';

const { Option } = Select;

/**
 * 通用时间范围选择器
 * 选项: 2h, 6h, 8h, 12h, 24h, 3d, 7d, All
 */
const TimeRangeSelect = ({ value, onChange, style, ...props }) => {
    return (
        <Select
            value={value}
            onChange={onChange}
            style={{ width: 120, ...style }}
            title="筛选基于新闻发布时间 (北京时间)"
            {...props}
        >
            <Option value={2}>2小时内</Option>
            <Option value={6}>6小时内</Option>
            <Option value={8}>8小时内</Option>
            <Option value={12}>12小时内</Option>
            <Option value={24}>24小时内</Option>
            <Option value={72}>3天内</Option>
            <Option value={168}>7天内</Option>
            <Option value={0}>全部时间</Option>
        </Select>
    );
};

TimeRangeSelect.propTypes = {
    value: PropTypes.number,
    onChange: PropTypes.func.isRequired,
    style: PropTypes.object
};

TimeRangeSelect.defaultProps = {
    value: 8
};

export default TimeRangeSelect;
