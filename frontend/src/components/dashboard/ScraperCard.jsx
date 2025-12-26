import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import { Card, Col, Select, Button, Tag } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined } from '@ant-design/icons';

const { Option } = Select;

/**
 * 爬虫控制卡片组件
 * 用于显示单个爬虫的状态和控制面板
 */
const ScraperCard = ({ name, status, onRun, onCancel, onConfigChange }) => {
    const isRunning = status.status === 'running';

    // Optimistic UI: Initialize with props, but allow immediate local input
    const [localLimit, setLocalLimit] = useState(status.limit || 5);
    const [localInterval, setLocalInterval] = useState(() => {
        if (status.interval) return String(status.interval);
        return "15"; // Default if undefined
    });

    useEffect(() => {
        if (status.limit !== undefined) {
            setLocalLimit(status.limit);
        }
        if (status.interval !== undefined) {
            setLocalInterval(String(status.interval));
        }
    }, [status.limit, status.interval]);

    // Console Auto-scroll Logic
    const logContainerRef = useRef(null);
    const [shouldAutoScroll, setShouldAutoScroll] = useState(true);

    useEffect(() => {
        if (shouldAutoScroll && logContainerRef.current) {
            logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
        }
    }, [status.logs, shouldAutoScroll]);

    const handleScroll = () => {
        if (logContainerRef.current) {
            const { scrollTop, scrollHeight, clientHeight } = logContainerRef.current;
            // tolerance of 10px
            const isAtBottom = scrollHeight - scrollTop - clientHeight < 20;
            setShouldAutoScroll(isAtBottom);
        }
    };

    const handleConfigUpdate = (key, val) => {
        if (key === 'limit') setLocalLimit(val);
        if (key === 'interval') setLocalInterval(val);
        onConfigChange(name, { [key]: val });
    };

    return (
        <Col span={8}>
            <Card
                title={name}
                extra={<Tag color={isRunning ? 'processing' : (status.status === 'error' ? 'error' : 'success')}>{status.status || 'Ready'}</Tag>}
            >
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
                    <span style={{ fontSize: 12 }}>限制条数:</span>
                    <Select
                        listHeight={180}
                        value={localLimit}
                        style={{ width: 80 }}
                        size="small"
                        onChange={(val) => handleConfigUpdate('limit', val)}
                    >
                        <Option value={5}>5</Option>
                        <Option value={10}>10</Option>
                        <Option value={15}>15</Option>
                        <Option value={20}>20</Option>
                        <Option value={30}>30</Option>
                    </Select>

                    <span style={{ fontSize: 12 }}>频率:</span>
                    <Select
                        listHeight={180}
                        value={localInterval}
                        style={{ width: 90 }}
                        size="small"
                        onChange={(val) => handleConfigUpdate('interval', val)}
                    >
                        <Option value="manual">手动</Option>
                        <Option value="15">15分钟</Option>
                        <Option value="30">30分钟</Option>
                        <Option value="60">1小时</Option>
                        <Option value="120">2小时</Option>
                        <Option value="180">3小时</Option>
                        <Option value="300">5小时</Option>
                    </Select>

                    {isRunning ? (
                        <Button
                            type="primary"
                            danger
                            size="small"
                            icon={<PauseCircleOutlined />}
                            onClick={() => onCancel(name)}
                        >
                            停止
                        </Button>
                    ) : (
                        <Button
                            type="primary"
                            size="small"
                            icon={<PlayCircleOutlined />}
                            loading={isRunning}
                            onClick={() => onRun(name, localLimit)}
                        >
                            运行
                        </Button>
                    )}
                </div>

                <div
                    ref={logContainerRef}
                    onScroll={handleScroll}
                    style={{
                        background: '#000',
                        color: '#0f0',
                        padding: '8px 12px',
                        borderRadius: 4,
                        fontSize: 12,
                        height: 150,
                        overflowY: 'auto',
                        fontFamily: 'monospace'
                    }}
                >
                    <div style={{ color: '#8c8c8c', marginBottom: 4, borderBottom: '1px solid #333', paddingBottom: 4 }}>
                        &gt; CONSOLE OUTPUT
                    </div>
                    {status.logs && status.logs.length > 0 ? (
                        status.logs.map((log, idx) => (
                            <div key={idx} style={{ lineHeight: '1.4', whiteSpace: 'pre-wrap' }}>{log}</div>
                        ))
                    ) : (
                        <div style={{ color: '#666', textAlign: 'center', marginTop: 40 }}>
                            {status.status === 'idle' && status.last_result ? status.last_result : 'WAITING FOR LOGS...'}
                        </div>
                    )}
                </div>
            </Card>
        </Col>
    );
};

ScraperCard.propTypes = {
    spider: PropTypes.shape({
        name: PropTypes.string.isRequired,
        url: PropTypes.string.isRequired,
        interval: PropTypes.number,
        limit: PropTypes.number
    }).isRequired,
    status: PropTypes.object,
    onRun: PropTypes.func.isRequired,
    onCancel: PropTypes.func.isRequired,
    onUpdateConfig: PropTypes.func.isRequired
};

export default ScraperCard;
