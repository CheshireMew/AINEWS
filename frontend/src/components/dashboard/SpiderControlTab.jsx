import React from 'react';
import PropTypes from 'prop-types';
import { Row, Col } from 'antd';
import ScraperCard from './ScraperCard';

/**
 * 爬虫控制Tab组件
 * 用于管理所有爬虫的运行状态和配置
 */
const SpiderControlTab = ({ spiders, spiderStatus, onRun, onCancel, onConfigChange }) => {
    return (
        <Row gutter={[16, 16]}>
            {spiders.map(name => (
                <ScraperCard
                    key={name}
                    name={name}
                    status={spiderStatus[name] || {}}
                    onRun={onRun}
                    onCancel={onCancel}
                    onConfigChange={onConfigChange}
                />
            ))}
        </Row>
    );
};

SpiderControlTab.propTypes = {
    spiders: PropTypes.arrayOf(PropTypes.object).isRequired,
    spiderStatus: PropTypes.object.isRequired,
    onRunSpider: PropTypes.func.isRequired,
    onCancelSpider: PropTypes.func.isRequired,
    onUpdateConfig: PropTypes.func.isRequired
};

export default SpiderControlTab;
