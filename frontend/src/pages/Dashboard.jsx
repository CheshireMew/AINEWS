import AIFilterTab from '../components/dashboard/AIFilterTab';
import AIBestTab from '../components/dashboard/AIBestTab';
import SpiderControlTab from '../components/dashboard/SpiderControlTab';
import FilterSettingsTab from '../components/dashboard/FilterSettingsTab';
import NewsManagementTab from '../components/dashboard/NewsManagementTab';
import DuplicateTreeTab from '../components/dashboard/DuplicateTreeTab';
import DeduplicatedTab from '../components/dashboard/DeduplicatedTab';
import CuratedNewsTab from '../components/dashboard/CuratedNewsTab';
import ApiSettingsTab from '../components/dashboard/ApiSettingsTab';
import React, { useEffect, useState, useRef } from 'react';
import {
    Layout, Menu, Button, Card, Row, Col,
    Statistic, Tag, Tabs, message, Select, Space, Input, Popconfirm,
    DatePicker, Modal, Checkbox, Segmented
} from 'antd';
import {
    LogoutOutlined, ReloadOutlined, RobotOutlined,
    DatabaseOutlined, PlayCircleOutlined, PauseCircleOutlined, PlusOutlined,
    DownloadOutlined, AppstoreOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { getStats, getNews, runSpider, getSpiders, getSpiderStatus, deleteNews, cancelScraper, updateConfig, deduplicateNews, getDeduplicatedNews, deleteDeduplicatedNews, getBlacklist, addBlacklist, deleteBlacklist, filterNews, exportNews, getCuratedNews, getCuratedStats, deleteCuratedNews, restoreNews, getFilteredDedupNews, getTelegramConfig, setTelegramConfig, testTelegramPush, filterCuratedNews, getFilteredCurated, getDeepSeekConfig, setDeepSeekConfig, testDeepSeekConnection, restoreCuratedNews, getAiConfig, setAiConfig, batchRestoreCurated, clearAllAiStatus, getExportNews } from '../api';
import * as api from '../api'; // Add api namespace import for fetchGlobalCounts
import ExportTab from '../components/dashboard/ExportTab';
import dayjs from 'dayjs'; // Import dayjs


const { Header, Content } = Layout;
const { Option } = Select;

import TimeRangeSelect from '../components/dashboard/TimeRangeSelect';

const Dashboard = () => {
    const navigate = useNavigate();
    const [stats, setStats] = useState([]);
    const [spiders, setSpiders] = useState([]);
    const [spiderStatus, setSpiderStatus] = useState({});
    const [activeKey, setActiveKey] = useState('1');
    const [contentType, setContentType] = useState('news'); // 'news' or 'article'

    // AI Filter State
    const [aiFilterPrompt, setAiFilterPrompt] = useState('');
    const [aiFilterHours, setAiFilterHours] = useState(8);
    const [aiFiltering, setAiFiltering] = useState(false);

    // 手动加精功能（全局状态，供多个Tab共享）
    const [manuallyFeatured, setManuallyFeatured] = useState([]);

    // 添加到加精列表
    const handleAddToFeatured = (record) => {
        // 先检查是否已存在
        const exists = manuallyFeatured.find(n => n.id === record.id);
        if (exists) {
            message.warning('此新闻已在加精列表中');
            return;
        }
        // 添加到列表
        setManuallyFeatured(prev => [record, ...prev]);
        message.success('已加精到新闻输出');
    };

    const fetchStats = async () => {
        try {
            const res = await getStats(contentType);
            setStats(res.data.stats || []);
        } catch (e) {
            console.error(e);
        }
    };



    const fetchSpiders = async () => {
        try {
            const res = await getSpiders();
            setSpiders(res.data.spiders || []);
        } catch (e) {
            console.error(e);
        }
    };

    useEffect(() => {
        fetchStats();
        fetchSpiders();
    }, []);

    // Refresh stats when contentType changes
    useEffect(() => {
        fetchStats();
    }, [contentType]);


    useEffect(() => {
        const fetchSpiderStatus = async () => {
            try {
                const res = await getSpiderStatus();
                // Backend returns spider status dict directly, not wrapped in {spiders: ...}
                const newStatus = res.data || {};

                // Merge new status with existing status to preserve logs
                setSpiderStatus(prevStatus => {
                    const merged = { ...prevStatus };
                    for (const [spider, status] of Object.entries(newStatus)) {
                        const prevSpider = prevStatus[spider] || {};
                        merged[spider] = {
                            ...prevSpider,
                            ...status,
                            // Preserve logs: use new logs only if they have content, otherwise keep old logs
                            logs: (status.logs && status.logs.length > 0)
                                ? status.logs
                                : (prevSpider.logs || [])
                        };
                    }
                    return merged;
                });
            } catch (e) {
                console.error(e);
            }
        };
        fetchSpiderStatus();
        const interval = setInterval(fetchSpiderStatus, 3000);
        return () => clearInterval(interval);
    }, [contentType]);

    const handleLogout = () => {
        localStorage.removeItem('token');
        window.location.href = '/login';
    };

    // 全局计数状态
    const [globalCounts, setGlobalCounts] = useState({
        news: 0,
        dedup: 0,
        filtered: 0,
        curated: 0,
        rejected: 0,
        approved: 0
    });

    // 获取全局计数
    const fetchGlobalCounts = async () => {
        try {
            const [newsRes, dedupRes, filteredRes, curatedRes, rejectedRes, approvedRes] = await Promise.all([
                api.getNews(1, 1, null, null, null, contentType),
                api.getDeduplicatedNews(1, 1, null, null, contentType),
                api.getFilteredDedupNews(1, 1, null, contentType),
                // Curated Data Tab now shows 'verified' deduplicated data
                api.getDeduplicatedNews(1, 1, null, null, contentType, 'verified'),
                api.getFilteredCurated('rejected', 1, 1, null, null, contentType),
                api.getFilteredCurated('approved', 1, 1, null, null, contentType)
            ]);

            setGlobalCounts({
                news: newsRes.data.total || 0,
                dedup: dedupRes.data.total || 0,
                filtered: filteredRes.data.total || 0,
                curated: curatedRes.data.total || 0,
                rejected: rejectedRes.data.total || 0,
                approved: approvedRes.data.total || 0
            });
        } catch (error) {
            console.error("Failed to fetch global counts:", error);
        }
    };

    useEffect(() => {
        fetchGlobalCounts();
        const interval = setInterval(fetchGlobalCounts, 30000); // 30s auto refresh
        return () => clearInterval(interval);
    }, [contentType]); // Re-fetch counts when content type changes



    const handleRunSpider = async (name, items) => {
        try {
            await runSpider(name, items);
            message.success(`已触发爬虫: ${name} (Max ${items})`);
            const res = await getSpiderStatus();
            setSpiderStatus(res.data);
        } catch (e) {
            console.error("Run Failed:", e);
            message.error(`触发失败: ${name}`);
        }
    };

    const handleStopSpider = async (name) => {
        try {
            await cancelScraper(name);
            message.warning(`已请求停止爬虫: ${name}`);
        } catch (e) {
            message.error(`停止失败: ${name}`);
        }
    }

    const handleConfigChange = async (name, changes) => {
        try {
            await updateConfig(name, changes);
            message.success(`已更新配置: ${name}`);
            const res = await getSpiderStatus();
            setSpiderStatus(res.data);
        } catch (e) {
            message.error('更新配置失败');
        }
    };



    // Blacklist Logic


    // Export Logic
    const [exportVisible, setExportVisible] = useState(false);
    const [exportLoading, setExportLoading] = useState(false);
    // Default last 24 hours
    const [exportDates, setExportDates] = useState([dayjs().subtract(1, 'day'), dayjs()]);
    const [exportKeyword, setExportKeyword] = useState('');
    const [exportTargetStage, setExportTargetStage] = useState('raw');
    const [exportFields, setExportFields] = useState(['title', 'source_site', 'published_at', 'source_url', 'content']);

    const handleShowExport = (defaultStage = 'raw') => {
        setExportTargetStage(defaultStage);
        // Reset or keep previous? Let's keep previous selection for convenience, or reset dates to fresh.
        setExportDates([dayjs().subtract(1, 'day'), dayjs()]);
        setExportVisible(true);
    };

    const handleExport = async () => {
        setExportLoading(true);
        try {
            const params = {};
            if (exportDates && exportDates.length === 2) {
                // Formatting for backend? API expects ISO string. Dayjs .toISOString() works.
                // FIX: DB uses 'YYYY-MM-DD HH:mm:ss' (Local/Beijing Time). toISOString sends UTC with 'T' which breaks comparison.
                params.start_date = exportDates[0].format('YYYY-MM-DD HH:mm:ss');
                params.end_date = exportDates[1].format('YYYY-MM-DD HH:mm:ss');
            }
            if (exportKeyword) params.keyword = exportKeyword;
            params.stage = exportTargetStage;

            if (exportFields && exportFields.length > 0) {
                params.fields = exportFields.join(',');
            }

            const res = await exportNews(params);

            // Create download link
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `ainews_export_${exportTargetStage}_${new Date().getTime()}.json`);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);

            setExportVisible(false);
            message.success('导出成功');
        } catch (e) {
            console.error(e);
            message.error('导出失败');
        } finally {
            setExportLoading(false);
        }
    };




    return (
        <Layout className="layout" style={{ minHeight: '100vh' }}>
            <Header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ color: 'white', fontSize: '20px', fontWeight: 'bold' }}>AINews Admin</div>
                <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                    <Segmented
                        options={[
                            { label: '⚡️ 快讯 (News)', value: 'news' },
                            { label: '📄 深度文章 (Articles)', value: 'article' }
                        ]}
                        value={contentType}
                        onChange={setContentType}
                    />
                    <Button type="primary" danger icon={<LogoutOutlined />} onClick={handleLogout}>
                        退出
                    </Button>
                </div>
            </Header>
            <Content style={{ padding: '20px 50px' }}>

                {/* Stats Section */}
                <div style={{ marginBottom: 20 }}>
                    <Row gutter={[16, 16]}>
                        {stats.map(s => (
                            <Col span={4} xl={3} key={s.source}>
                                <Card size="small">
                                    <Statistic
                                        title={s.source}
                                        value={s.count}
                                        formatter={(val) => <span style={{ color: '#3f8600' }}>{val}</span>}
                                        prefix={<DatabaseOutlined />}
                                    />
                                </Card>
                            </Col>
                        ))}
                    </Row>
                </div>

                <div style={{ background: '#fff', padding: 24, minHeight: 280 }}>
                    <Tabs
                        destroyOnHidden={false}
                        activeKey={activeKey}
                        onChange={(key) => {
                            setActiveKey(key);
                            // 切换Tab时仅刷新全局计数（Badge）和统计
                            fetchGlobalCounts();
                            if (key === '1') {
                                fetchStats();
                            }
                        }}
                        items={[
                            {
                                key: '1',
                                label: <span><DatabaseOutlined />数据管理 ({globalCounts.news})</span>,
                                children: <NewsManagementTab spiders={spiders} onShowExport={handleShowExport} contentType={contentType} />
                            },
                            {
                                key: '1.5',
                                label: <span><AppstoreOutlined />重复对照</span>,
                                children: <DuplicateTreeTab spiders={spiders} onShowExport={handleShowExport} contentType={contentType} />
                            },
                            {
                                key: '3',
                                label: <span><DatabaseOutlined />去重数据 ({globalCounts.dedup})</span>,
                                children: <DeduplicatedTab spiders={spiders} onAddToFeatured={handleAddToFeatured} onShowExport={handleShowExport} contentType={contentType} />
                            },
                            {
                                key: '4',
                                label: <span><DatabaseOutlined />过滤设置 ({globalCounts.filtered})</span>,
                                children: <FilterSettingsTab onAddToFeatured={handleAddToFeatured} active={activeKey === '4'} contentType={contentType} />
                            },
                            {
                                key: '5',
                                label: <span><DatabaseOutlined />精选数据 ({globalCounts.curated})</span>,
                                children: <CuratedNewsTab spiders={spiders} onAddToFeatured={handleAddToFeatured} onShowExport={handleShowExport} active={activeKey === '5'} contentType={contentType} />
                            },
                            {
                                key: '8',
                                label: <span><RobotOutlined />AI 筛选 ({globalCounts.rejected})</span>,
                                children: <AIFilterTab onAddToFeatured={handleAddToFeatured} contentType={contentType} />
                            },
                            {
                                key: '9',
                                label: <span><DatabaseOutlined />AI 精选 ({globalCounts.approved})</span>,
                                children: <AIBestTab spiders={spiders} onAddToFeatured={handleAddToFeatured} onShowExport={handleShowExport} contentType={contentType} />
                            },
                            {
                                key: '2',
                                label: <span><RobotOutlined />爬虫控制</span>,
                                children: (
                                    <SpiderControlTab
                                        spiders={spiders}
                                        spiderStatus={spiderStatus}
                                        onRun={handleRunSpider}
                                        onCancel={handleStopSpider}
                                        onConfigChange={handleConfigChange}
                                        contentType={contentType}
                                    />
                                )
                            },



                            // ... (in items array)
                            {
                                key: '6',
                                label: <span><RobotOutlined />API 配置</span>,
                                children: <ApiSettingsTab />
                            },
                            {
                                key: '7',
                                label: <span><DownloadOutlined />新闻输出</span>,
                                children: <ExportTab manuallyFeatured={manuallyFeatured} setManuallyFeatured={setManuallyFeatured} contentType={contentType} />
                            }
                        ]}
                    />
                </div>
            </Content>

            <Modal
                title="数据导出"
                open={exportVisible}
                onOk={handleExport}
                onCancel={() => setExportVisible(false)}
                confirmLoading={exportLoading}
            >
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    <div>
                        <span style={{ display: 'block', marginBottom: 8 }}>时间范围:</span>
                        <DatePicker.RangePicker
                            showTime
                            style={{ width: '100%' }}
                            value={exportDates}
                            onChange={(dates) => setExportDates(dates)}
                        />
                    </div>
                    <div>
                        <span style={{ display: 'block', marginBottom: 8 }}>关键词过滤 (可选):</span>
                        <Input
                            placeholder="输入关键词..."
                            value={exportKeyword}
                            onChange={e => setExportKeyword(e.target.value)}
                        />
                    </div>
                    <div>
                        <span style={{ display: 'block', marginBottom: 8 }}>数据阶段:</span>
                        <Select
                            value={exportTargetStage}
                            style={{ width: '100%' }}
                            onChange={setExportTargetStage}
                        >
                            <Option value="raw">原始数据 (Data Management)</Option>
                            <Option value="deduplicated">已去重数据 (Deduplicated)</Option>
                            <Option value="curated">精选数据 (Curated)</Option>
                            <Option value="filtered">已过滤数据 (Filtered)</Option>
                        </Select>
                    </div>

                    <div>
                        <span style={{ display: 'block', marginBottom: 8 }}>选择导出字段:</span>
                        <Checkbox.Group
                            options={[
                                { label: '标题', value: 'title' },
                                { label: '内容', value: 'content' },
                                { label: '发布时间', value: 'published_at' },
                                { label: '链接', value: 'source_url' },
                                { label: '来源', value: 'source_site' },
                                { label: 'ID', value: 'id' }
                            ]}
                            value={exportFields}
                            onChange={setExportFields}
                        />
                    </div>
                </div>
            </Modal>

        </Layout >
    );
};

export default Dashboard;
