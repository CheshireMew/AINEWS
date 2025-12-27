import AIFilterTab from '../components/dashboard/AIFilterTab';
import AIBestTab from '../components/dashboard/AIBestTab';
import SpiderControlTab from '../components/dashboard/SpiderControlTab';
import FilterSettingsTab from '../components/dashboard/FilterSettingsTab';
import NewsManagementTab from '../components/dashboard/NewsManagementTab';
import DeduplicatedTab from '../components/dashboard/DeduplicatedTab';
import CuratedNewsTab from '../components/dashboard/CuratedNewsTab';
import ApiSettingsTab from '../components/dashboard/ApiSettingsTab';
import React, { useEffect, useState, useRef } from 'react';
import {
    Layout, Menu, Button, Card, Row, Col,
    Statistic, Tag, Tabs, message, Select, Space, Input, Popconfirm,
    DatePicker, Modal, Checkbox
} from 'antd';
import {
    LogoutOutlined, ReloadOutlined, RobotOutlined,
    DatabaseOutlined, PlayCircleOutlined, PauseCircleOutlined, PlusOutlined,
    DownloadOutlined
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
    const [news, setNews] = useState([]);
    const [loading, setLoading] = useState(false);
    const [spiders, setSpiders] = useState([]);
    const [spiderStatus, setSpiderStatus] = useState({});
    const [activeKey, setActiveKey] = useState('1');

    // Pagination
    const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });
    const [filterSource, setFilterSource] = useState(null);



    // Deduplicated news
    const [dedupNews, setDedupNews] = useState([]);
    const [dedupPagination, setDedupPagination] = useState({ current: 1, pageSize: 20, total: 0 });
    const [dedupFilterSource, setDedupFilterSource] = useState(null);
    const [loadingDedup, setLoadingDedup] = useState(false);

    // AI Filter and Best Tab (pagination for tab labels)
    const [rejectedPagination, setRejectedPagination] = useState({ current: 1, pageSize: 20, total: 0 });
    const [approvedPagination, setApprovedPagination] = useState({ current: 1, pageSize: 20, total: 0 });

    // AI Filter State
    const [rejectedNews, setRejectedNews] = useState([]);
    const [rejectedLoading, setRejectedLoading] = useState(false);
    const [approvedNews, setApprovedNews] = useState([]);
    const [approvedLoading, setApprovedLoading] = useState(false);
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
            const res = await getStats();
            setStats(res.data.stats || []);
        } catch (e) {
            console.error(e);
        }
    };

    const fetchNews = async (page = 1, source = null) => {
        setLoading(true);
        try {
            const res = await getNews(page, pagination.pageSize, source);
            setNews(res.data.data);
            setPagination({
                ...pagination,
                current: page,
                total: res.data.total
            });
        } catch (e) {
            message.error('加载新闻失败');
        } finally {
            setLoading(false);
        }
    };

    const fetchDedupNews = async (page = 1, source = null) => {
        setLoadingDedup(true);
        try {
            const res = await getDeduplicatedNews(page, dedupPagination.pageSize, source);
            setDedupNews(res.data.data);
            setDedupPagination({
                ...dedupPagination,
                current: page,
                total: res.data.total
            });
        } catch (e) {
            message.error('加载去重数据失败');
        } finally {
            setLoadingDedup(false);
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
        fetchNews(1, filterSource);
        fetchSpiders();

        // 初始化时加载所有数据的第一页以获取统计数量
        fetchDedupNews(1, null);
        fetchCuratedNews(1, null);
        fetchFilteredNews(1);
        fetchRejectedNews(1);
        fetchApprovedNews(1);

        const fetchSpiderStatus = async () => {
            try {
                const res = await getSpiderStatus();
                setSpiderStatus(res.data);
            } catch (e) {
                console.error(e);
            }
        };
        fetchSpiderStatus();
        const interval = setInterval(fetchSpiderStatus, 3000);
        return () => clearInterval(interval);
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
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
            // Parallel requests for counts (limit=1 is enough to get 'total')
            const [newsRes, dedupRes, filteredRes, curatedRes, rejectedRes, approvedRes] = await Promise.all([
                api.getNews({ page: 1, limit: 1 }),
                api.getDeduplicatedNews({ page: 1, limit: 1 }),
                api.getFilteredDedupNews({ page: 1, limit: 1 }),
                api.getCuratedNews({ page: 1, limit: 1 }),
                api.getFilteredCurated('rejected', 1, 1),  // Use positional params
                api.getFilteredCurated('approved', 1, 1)   // Use positional params
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

    // 初始加载和定期刷新计数
    useEffect(() => {
        fetchGlobalCounts();
        const interval = setInterval(fetchGlobalCounts, 30000); // 30s auto refresh
        return () => clearInterval(interval);
    }, []);

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


    // Filtered News View
    const [filteredNews, setFilteredNews] = useState([]);
    const [filteredPagination, setFilteredPagination] = useState({ current: 1, pageSize: 20, total: 0 });
    const [loadingFiltered, setLoadingFiltered] = useState(false);

    // Curated News View
    const [curatedNews, setCuratedNews] = useState([]);
    const [curatedPagination, setCuratedPagination] = useState({ current: 1, pageSize: 20, total: 0 });
    const [loadingCurated, setLoadingCurated] = useState(false);
    const [curatedFilterSource, setCuratedFilterSource] = useState(null);

    const fetchFilteredNews = async (page = 1) => {
        setLoadingFiltered(true);
        try {
            // Fetch filtered news from deduplicated_news table
            const res = await getFilteredDedupNews(page, filteredPagination.pageSize);
            setFilteredNews(res.data.data);
            setFilteredPagination({
                ...filteredPagination,
                current: page,
                total: res.data.total
            });
        } catch (e) {
            console.error("Fetch filtered news failed", e);
        } finally {
            setLoadingFiltered(false);
        }
    };

    const fetchCuratedNews = async (page = 1, source = null) => {
        setLoadingCurated(true);
        try {
            const res = await getCuratedNews(page, curatedPagination.pageSize, source);
            setCuratedNews(res.data.data);
            setCuratedPagination({
                ...curatedPagination,
                current: page,
                total: res.data.total
            });
        } catch (e) {
            console.error("Fetch curated news failed", e);
        } finally {
            setLoadingCurated(false);
        }
    };





    // Import API
    // (Note: imports are at top level, assuming they are added)


    const fetchRejectedNews = async (page = 1) => {
        setRejectedLoading(true);
        try {
            const res = await getFilteredCurated('rejected', page, rejectedPagination.pageSize);
            setRejectedNews(res.data.data);
            setRejectedPagination({
                ...rejectedPagination,
                current: page,
                total: res.data.total
            });
        } catch (e) {
            message.error('加载被拒绝数据失败');
        } finally {
            setRejectedLoading(false);
        }
    };
    const fetchApprovedNews = async (page = 1) => {
        setApprovedLoading(true);
        try {
            const res = await getFilteredCurated('approved', page, approvedPagination.pageSize);
            setApprovedNews(res.data.data);
            setApprovedPagination({
                ...approvedPagination,
                current: page,
                total: res.data.total
            });
        } catch (e) {
            message.error('加载精选数据失败');
        } finally {
            setApprovedLoading(false);
        }
    };




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
                <Button type="primary" danger icon={<LogoutOutlined />} onClick={handleLogout}>
                    退出
                </Button>
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
                        activeKey={activeKey}
                        onChange={(key) => {
                            setActiveKey(key);
                            // 切换Tab时立即刷新全局计数
                            fetchGlobalCounts();

                            if (key === '1') {
                                fetchNews(1, filterSource);
                                fetchStats();
                            } else if (key === '3') { // Deduplicated Data
                                fetchDedupNews(1, dedupFilterSource);
                            } else if (key === '5') { // Curated Data
                                fetchCuratedNews(1, curatedFilterSource);
                            } else if (key === '7') { // News Export
                                // 新闻输出tab，无需自动加载数据（用户手动点击加载按钮）
                            } else if (key === '8') { // AI Filter Tab
                                fetchRejectedNews(1);
                            } else if (key === '9') { // AI Best Tab
                                fetchApprovedNews(1);
                            }
                        }}
                        items={[
                            {
                                key: '1',
                                label: <span><DatabaseOutlined />数据管理 ({globalCounts.news})</span>,
                                children: <NewsManagementTab spiders={spiders} onShowExport={handleShowExport} />
                            },
                            {
                                key: '3',
                                label: <span><DatabaseOutlined />去重数据 ({globalCounts.dedup})</span>,
                                children: <DeduplicatedTab spiders={spiders} onAddToFeatured={handleAddToFeatured} onShowExport={handleShowExport} />
                            },
                            {
                                key: '4',
                                label: <span><DatabaseOutlined />过滤设置 ({globalCounts.filtered})</span>,
                                children: <FilterSettingsTab onAddToFeatured={handleAddToFeatured} active={activeKey === '4'} />
                            },
                            {
                                key: '5',
                                label: <span><DatabaseOutlined />精选数据 ({globalCounts.curated})</span>,
                                children: <CuratedNewsTab spiders={spiders} onAddToFeatured={handleAddToFeatured} onShowExport={handleShowExport} active={activeKey === '5'} />
                            },
                            {
                                key: '8',
                                label: <span><RobotOutlined />AI 筛选 ({globalCounts.rejected})</span>,
                                children: <AIFilterTab onAddToFeatured={handleAddToFeatured} />
                            },
                            {
                                key: '9',
                                label: <span><DatabaseOutlined />AI 精选 ({globalCounts.approved})</span>,
                                children: <AIBestTab spiders={spiders} onAddToFeatured={handleAddToFeatured} onShowExport={handleShowExport} />
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
                                children: <ExportTab manuallyFeatured={manuallyFeatured} setManuallyFeatured={setManuallyFeatured} />
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
