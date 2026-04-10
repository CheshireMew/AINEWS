import React from 'react';
import PropTypes from 'prop-types';
import { Button, Popconfirm } from 'antd';

import TimeRangeSelect from './TimeRangeSelect';

export default function BlocklistRunnerPanel({
    filterTimeRange,
    filtering,
    setFilterTimeRange,
    applyCurrentBlocklist,
    restoreAll,
}) {
    return (
        <div style={{ marginBottom: 20 }}>
            <h3>1. 执行黑名单拦截</h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                <TimeRangeSelect value={filterTimeRange} onChange={setFilterTimeRange} />
                <Button type="primary" onClick={applyCurrentBlocklist} loading={filtering}>
                    立即执行
                </Button>
                <Popconfirm
                    title="还原已拦截内容"
                    description="确定要还原所有已拦截内容吗？这会把内容放回归档池。"
                    onConfirm={restoreAll}
                    okText="确定"
                    cancelText="取消"
                >
                    <Button type="primary" danger>
                        还原已拦截内容
                    </Button>
                </Popconfirm>
                <span style={{ color: '#999', fontSize: 13 }}>
                    只扫描归档池中的内容，命中黑名单后会进入下方列表。
                </span>
            </div>
        </div>
    );
}

BlocklistRunnerPanel.propTypes = {
    filterTimeRange: PropTypes.number.isRequired,
    filtering: PropTypes.bool.isRequired,
    setFilterTimeRange: PropTypes.func.isRequired,
    applyCurrentBlocklist: PropTypes.func.isRequired,
    restoreAll: PropTypes.func.isRequired,
};
