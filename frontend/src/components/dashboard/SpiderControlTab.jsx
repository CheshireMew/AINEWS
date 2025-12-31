import React from 'react';
import PropTypes from 'prop-types';
import { Row } from 'antd';
import ScraperCard from './ScraperCard';

/**
 * 爬虫控制Tab组件
 * 用于管理所有爬虫的运行状态和配置
 * Updated: Force Refresh
 */
const SpiderControlTab = ({ spiders, spiderStatus, onRun, onCancel, onConfigChange, contentType }) => {
    // 根据 contentType 过滤爬虫
    const filteredSpiders = spiders.filter(spider => {
        // 如果 spider 是对象（新格式），检查 type
        if (typeof spider === 'object' && spider.type) {
            return spider.type === contentType;
        }
        // 兼容旧格式（字符串），默认为 news
        return contentType === 'news';
    });

    return (
        <div style={{ padding: '0 10px' }}>
            <Row gutter={[16, 16]}>
                {filteredSpiders.map(spider => {
                    const spiderName = typeof spider === 'object' ? spider.name : spider;
                    return (
                        <ScraperCard
                            key={spiderName}
                            name={spiderName}
                            status={spiderStatus[spiderName] || {}}
                            onRun={onRun}
                            onCancel={onCancel}
                            onConfigChange={onConfigChange}
                        />
                    );
                })}
            </Row>
        </div>
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
