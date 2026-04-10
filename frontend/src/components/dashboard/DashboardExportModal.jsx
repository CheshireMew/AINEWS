import React from 'react';
import PropTypes from 'prop-types';
import { Modal, DatePicker, Input, Select, Checkbox } from 'antd';

import { DASHBOARD_EXPORT_OPTIONS } from '../../contracts/content';

const { Option } = Select;

export default function DashboardExportModal({ exportState }) {
    return (
        <Modal
            title="数据导出"
            open={exportState.visible}
            onOk={exportState.submit}
            onCancel={exportState.close}
            confirmLoading={exportState.loading}
        >
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div>
                    <span style={{ display: 'block', marginBottom: 8 }}>时间范围:</span>
                    <DatePicker.RangePicker
                        showTime
                        style={{ width: '100%' }}
                        value={exportState.dates}
                        onChange={exportState.setDates}
                    />
                </div>
                <div>
                    <span style={{ display: 'block', marginBottom: 8 }}>关键词过滤:</span>
                    <Input
                        placeholder="输入关键词..."
                        value={exportState.keyword}
                        onChange={(event) => exportState.setKeyword(event.target.value)}
                    />
                </div>
                <div>
                    <span style={{ display: 'block', marginBottom: 8 }}>数据区域:</span>
                    <Select value={exportState.scope} style={{ width: '100%' }} onChange={exportState.setScope}>
                        {DASHBOARD_EXPORT_OPTIONS.map((option) => (
                            <Option key={option.value} value={option.value}>{option.label}</Option>
                        ))}
                    </Select>
                </div>
                <div>
                    <span style={{ display: 'block', marginBottom: 8 }}>导出字段:</span>
                    <Checkbox.Group
                        options={[
                            { label: '标题', value: 'title' },
                            { label: '内容', value: 'content' },
                            { label: '发布时间', value: 'published_at' },
                            { label: '链接', value: 'source_url' },
                            { label: '来源', value: 'source_site' },
                            { label: 'ID', value: 'id' }
                        ]}
                        value={exportState.fields}
                        onChange={exportState.setFields}
                    />
                </div>
            </div>
        </Modal>
    );
}

DashboardExportModal.propTypes = {
    exportState: PropTypes.shape({
        visible: PropTypes.bool.isRequired,
        loading: PropTypes.bool.isRequired,
        dates: PropTypes.any,
        keyword: PropTypes.string.isRequired,
        scope: PropTypes.string.isRequired,
        fields: PropTypes.arrayOf(PropTypes.string).isRequired,
        submit: PropTypes.func.isRequired,
        close: PropTypes.func.isRequired,
        setDates: PropTypes.func.isRequired,
        setKeyword: PropTypes.func.isRequired,
        setScope: PropTypes.func.isRequired,
        setFields: PropTypes.func.isRequired,
    }).isRequired,
};
