import React, { useEffect, useState, useRef } from 'react';
import {
    Layout, Menu, Table, Button, Card, Row, Col,
    Statistic, Tag, Tabs, message, Select, Space, Input, Popconfirm,
    DatePicker, Modal, Checkbox
} from 'antd';
import {
    LogoutOutlined, ReloadOutlined, RobotOutlined,
    DatabaseOutlined, PlayCircleOutlined, PauseCircleOutlined, PlusOutlined,
    DownloadOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { getStats, getNews, runSpider, getSpiders, getSpiderStatus, deleteNews, cancelScraper, updateConfig, deduplicateNews, getDeduplicatedNews, deleteDeduplicatedNews, getBlacklist, addBlacklist, deleteBlacklist, filterNews, exportNews, getCuratedNews, getCuratedStats, deleteCuratedNews, restoreNews, getFilteredDedupNews, getTelegramConfig, setTelegramConfig, testTelegramPush } from '../api';
import dayjs from 'dayjs'; // Import dayjs


const { Header, Content } = Layout;
const { Option } = Select;

// Scraper Control Card Component
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

const Dashboard = () => {
    const navigate = useNavigate();
    const [stats, setStats] = useState([]);
    const [news, setNews] = useState([]);
    const [loading, setLoading] = useState(false);
    const [spiders, setSpiders] = useState([]);
    const [spiderStatus, setSpiderStatus] = useState({});

    // Pagination
    const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });
    const [filterSource, setFilterSource] = useState(null);

    // Deduplication
    const [deduplicating, setDeduplicating] = useState(false);
    const [dedupTimeRange, setDedupTimeRange] = useState(6); // Default 6 hours (User Request)

    // Deduplicated news
    const [dedupNews, setDedupNews] = useState([]);
    const [dedupPagination, setDedupPagination] = useState({ current: 1, pageSize: 20, total: 0 });
    const [dedupFilterSource, setDedupFilterSource] = useState(null);
    const [loadingDedup, setLoadingDedup] = useState(false);

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

    const handleDeleteNews = async (id) => {
        try {
            await deleteNews(id);
            message.success('删除成功');
            fetchNews(pagination.current, filterSource);
        } catch (e) {
            message.error('删除失败');
        }
    };

    const handleDeleteDedupNews = async (newsId) => {
        try {
            await deleteDeduplicatedNews(newsId);
            message.success('删除成功');
            fetchDedupNews(dedupPagination.current, dedupFilterSource);
        } catch (e) {
            message.error('删除失败');
        }
    };

    const handleDeduplicate = async () => {
        setDeduplicating(true);
        try {
            const res = await deduplicateNews(dedupTimeRange, 'mark');
            const stats = res.data.stats;
            message.success(
                `去重完成！扫描 ${stats.total_scanned} 条，发现 ${stats.duplicates_found} 条重复，` +
                `已标记 ${stats.duplicates_processed} 条，归档 ${stats.archived_count} 条原始数据`
            );
            fetchStats();
            fetchNews(pagination.current, filterSource);
        } catch (e) {
            message.error('去重失败: ' + (e.response?.data?.detail || e.message));
        } finally {
            setDeduplicating(false);
        }
    };

    // Blacklist Logic
    const [blacklistKeywords, setBlacklistKeywords] = useState([]);
    const [newKeyword, setNewKeyword] = useState('');
    const [newMatchType, setNewMatchType] = useState('contains');
    const [filtering, setFiltering] = useState(false);
    const [filterTimeRange, setFilterTimeRange] = useState(24);

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

    const handleRestoreNews = async (id) => {
        try {
            await restoreNews(id, 'deduplicated_news');
            message.success('还原成功');
            fetchFilteredNews(filteredPagination.current);
        } catch (e) {
            message.error('还原失败');
        }
    };

    const handleDeleteCuratedNews = async (id) => {
        try {
            await deleteCuratedNews(id);
            message.success('删除成功');
            fetchCuratedNews(curatedPagination.current, curatedFilterSource);
        } catch (e) {
            message.error('删除失败');
        }
    };

    const fetchBlacklistData = async () => {
        try {
            const res = await getBlacklist();
            setBlacklistKeywords(res.data.keywords || []);
        } catch (e) {
            console.error("Fetch blacklist failed", e);
        }
    };

    const handleAddKeyword = async () => {
        if (!newKeyword.trim()) return;
        try {
            await addBlacklist(newKeyword.trim(), newMatchType);
            message.success('添加成功');
            setNewKeyword('');
            fetchBlacklistData();
        } catch (e) {
            message.error('添加失败，可能是重复词');
        }
    };

    const handleDeleteKeyword = async (id) => {
        try {
            await deleteBlacklist(id);
            message.success('删除成功');
            fetchBlacklistData();
        } catch (e) {
            message.error('删除失败');
        }
    };

    const handleFilterNews = async () => {
        setFiltering(true);
        try {
            const res = await filterNews(filterTimeRange);
            const stats = res.data.stats;
            message.success(`过滤完成！扫描 ${stats.scanned} 条，标记过滤 ${stats.filtered} 条`);
            fetchStats(); // Update stats if any
        } catch (e) {
            message.error('过滤任务执行失败');
        } finally {
            setFiltering(false);
        }
    };

    // --- Telegram Logic ---
    const [telegramConfig, setTelegramConfigState] = useState({ bot_token: '', chat_id: '', enabled: false });

    useEffect(() => {
        fetchTelegramConfig();
    }, []);

    const fetchTelegramConfig = async () => {
        try {
            const res = await getTelegramConfig();
            setTelegramConfigState(res.data);
        } catch (error) {
            console.error("Failed to fetch Telegram config", error);
        }
    };

    const handleSaveTelegramConfig = async () => {
        try {
            await setTelegramConfig(telegramConfig);
            message.success("Telegram 配置已保存");
        } catch (error) {
            message.error("保存失败: " + (error.response?.data?.detail || error.message));
        }
    };

    const handleTestTelegramPush = async () => {
        try {
            await testTelegramPush();
            message.success("测试消息发送成功，请检查 Telegram");
        } catch (error) {
            message.error("测试发送失败: " + (error.response?.data?.detail || error.message));
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


    const blacklistColumns = [
        { title: '关键词', dataIndex: 'keyword', key: 'keyword', render: text => <Tag color="red">{text}</Tag> },
        {
            title: '匹配模式',
            dataIndex: 'match_type',
            key: 'match_type',
            render: text => <Tag color={text === 'regex' ? 'purple' : 'blue'}>{text}</Tag>
        },
        { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
        {
            title: '操作',
            key: 'action',
            render: (_, record) => (
                <Popconfirm title="确定删除？" onConfirm={() => handleDeleteKeyword(record.id)}>
                    <Button type="link" danger size="small">删除</Button>
                </Popconfirm>
            )
        },
    ];



    const columns = [
        { title: 'ID', dataIndex: 'id', width: 60 },
        {
            title: '标题', dataIndex: 'title',
            render: (text, record) => <a href={record.source_url} target="_blank" rel="noopener noreferrer">{text}</a>
        },
        {
            title: '来源', dataIndex: 'source_site', width: 100,
            render: text => <Tag color="blue">{text}</Tag>
        },
        {
            title: '状态', dataIndex: 'stage', width: 90,
            render: (stage) => {
                if (stage === 'duplicate') {
                    return <Tag color="red">重复</Tag>;
                } else {
                    return <Tag color="default">原始</Tag>;
                }
            }
        },
        {
            title: '发布时间', dataIndex: 'published_at', width: 160,
            render: text => {
                const date = new Date(text);
                return isNaN(date.getTime()) ? text : date.toLocaleString();
            }
        },
        {
            title: '操作', width: 80,
            render: (_, record) => (
                <Button
                    type="link"
                    danger
                    size="small"
                    onClick={() => handleDeleteNews(record.id)}
                >
                    删除
                </Button>
            )
        }
    ];

    // 去重数据专用列定义
    const dedupColumns = [
        { title: 'ID', dataIndex: 'id', width: 60 },
        {
            title: '标题', dataIndex: 'title', ellipsis: true,
            render: (text, record) => <a href={record.source_url} target="_blank" rel="noopener noreferrer">{text}</a>
        },
        { title: '来源', dataIndex: 'source_site', width: 120 },
        {
            title: '发布时间', dataIndex: 'published_at', width: 160,
            render: text => {
                const date = new Date(text);
                return isNaN(date.getTime()) ? text : date.toLocaleString();
            }
        },
        {
            title: '归档时间', dataIndex: 'deduplicated_at', width: 160,
            render: text => {
                const date = new Date(text);
                return isNaN(date.getTime()) ? text : date.toLocaleString();
            }
        },
        {
            title: '操作', width: 80,
            render: (_, record) => (
                <Button
                    type="link"
                    danger
                    size="small"
                    onClick={() => handleDeleteDedupNews(record.id)}
                >
                    删除
                </Button>
            )
        }
    ];

    const curatedColumns = [
        { title: 'ID', dataIndex: 'id', width: 60 },
        { title: '标题', dataIndex: 'title', ellipsis: true, render: (text, record) => <a href={record.source_url} target="_blank" rel="noopener noreferrer">{text}</a> },
        { title: '来源', dataIndex: 'source_site', width: 120 },
        {
            title: '发布时间', dataIndex: 'published_at', width: 160,
            render: text => {
                const date = new Date(text);
                return isNaN(date.getTime()) ? text : date.toLocaleString();
            }
        },
        {
            title: '精选时间', dataIndex: 'curated_at', width: 160,
            render: text => {
                const date = new Date(text);
                return isNaN(date.getTime()) ? text : date.toLocaleString();
            }
        },
        {
            title: '操作', width: 80,
            render: (_, record) => (
                <Button
                    type="link"
                    danger
                    size="small"
                    onClick={() => handleDeleteCuratedNews(record.id)}
                >
                    删除
                </Button>
            )
        }
    ];

    const filteredColumns = [
        ...dedupColumns.filter(c => c.dataIndex !== 'deduplicated_at' && c.title !== '操作'),
        {
            title: '操作', width: 140,
            render: (_, record) => (
                <Space>
                    <Button
                        type="link"
                        size="small"
                        onClick={() => handleRestoreNews(record.id)}
                    >
                        还原
                    </Button>
                    <Button
                        type="link"
                        danger
                        size="small"
                        onClick={() => handleDeleteDedupNews(record.id)}
                    >
                        删除
                    </Button>
                </Space>
            )
        }
    ];

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
                        defaultActiveKey="1"
                        onChange={(key) => {
                            if (key === '1') {
                                fetchNews(1, filterSource);
                                fetchStats();
                            } else if (key === '3') { // Deduplicated Data
                                fetchDedupNews(1, dedupFilterSource);
                            } else if (key === '5') { // Curated Data
                                fetchCuratedNews(1, curatedFilterSource);
                            } else if (key === '4') { // Filter Settings
                                fetchBlacklistData();
                                fetchFilteredNews(1);
                            } else if (key === '6') { // Notification Settings
                                fetchTelegramConfig();
                            }
                        }}
                        items={[
                            {
                                key: '1',
                                label: <span><DatabaseOutlined />数据管理</span>,
                                children: (
                                    <>
                                        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
                                            <Space>
                                                <Select
                                                    style={{ width: 200 }}
                                                    placeholder="筛选来源"
                                                    allowClear
                                                    onChange={(val) => {
                                                        setFilterSource(val);
                                                        fetchNews(1, val);
                                                    }}
                                                >
                                                    {spiders.map(s => <Option key={s} value={s}>{s}</Option>)}
                                                </Select>

                                                <Button icon={<DownloadOutlined />} onClick={() => handleShowExport('raw')}>导出</Button>
                                            </Space>
                                            <Button icon={<ReloadOutlined />} onClick={() => fetchNews(pagination.current, filterSource)}>刷新</Button>
                                        </div>

                                        <Table
                                            columns={columns}
                                            dataSource={news}
                                            rowKey="id"
                                            loading={loading}
                                            pagination={{
                                                ...pagination,
                                                onChange: (page) => fetchNews(page, filterSource)
                                            }}
                                            expandable={{
                                                expandedRowRender: record => (
                                                    <div style={{ padding: 16, background: '#fafafa' }}>
                                                        <p><strong>URL:</strong> <a href={record.source_url} target="_blank">{record.source_url}</a></p>
                                                        <div style={{ whiteSpace: 'pre-wrap', maxHeight: 400, overflowY: 'auto' }}>
                                                            {record.content || <span style={{ color: '#ccc' }}>No content available</span>}
                                                        </div>
                                                    </div>
                                                ),
                                                rowExpandable: record => true,
                                            }}
                                        />
                                    </>
                                )
                            },
                            {
                                key: '3',
                                label: <span><DatabaseOutlined />去重数据</span>,
                                children: (
                                    <>
                                        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
                                            <Space>
                                                <span style={{ fontSize: 14 }}>来源筛选:</span>
                                                <Select
                                                    value={dedupFilterSource}
                                                    style={{ width: 150 }}
                                                    onChange={(val) => {
                                                        setDedupFilterSource(val);
                                                        fetchDedupNews(1, val);
                                                    }}
                                                    allowClear
                                                    placeholder="全部来源"
                                                >
                                                    {spiders.map(s => <Option key={s} value={s}>{s}</Option>)}
                                                </Select>

                                                <div style={{ borderLeft: '1px solid #d9d9d9', height: 32, margin: '0  8px' }} />

                                                <span style={{ fontSize: 14 }}>去重范围:</span>
                                                <Select
                                                    value={dedupTimeRange}
                                                    style={{ width: 110 }}
                                                    onChange={setDedupTimeRange}
                                                >
                                                    <Option value={6}>6小时内</Option>
                                                    <Option value={12}>12小时内</Option>
                                                    <Option value={24}>24小时内</Option>
                                                    <Option value={48}>48小时内</Option>
                                                </Select>
                                                <Button
                                                    type="primary"
                                                    onClick={handleDeduplicate}
                                                    loading={deduplicating}
                                                >
                                                    手动去重
                                                </Button>
                                                <Button icon={<DownloadOutlined />} onClick={() => handleShowExport('deduplicated')}>导出</Button>
                                            </Space>
                                            <Button icon={<ReloadOutlined />} onClick={() => fetchDedupNews(dedupPagination.current, dedupFilterSource)}>刷新</Button>
                                        </div>

                                        <Table
                                            columns={dedupColumns}
                                            dataSource={dedupNews}
                                            rowKey="id"
                                            loading={loadingDedup}
                                            pagination={{
                                                ...dedupPagination,
                                                showSizeChanger: false,
                                                onChange: (page) => fetchDedupNews(page, dedupFilterSource)
                                            }}
                                            expandable={{
                                                expandedRowRender: record => (
                                                    <div style={{ padding: 16, background: '#fafafa' }}>
                                                        <p><strong>URL:</strong> <a href={record.source_url} target="_blank">{record.source_url}</a></p>
                                                        <div style={{ whiteSpace: 'pre-wrap', maxHeight: 400, overflowY: 'auto' }}>
                                                            {record.content || <span style={{ color: '#ccc' }}>No content available</span>}
                                                        </div>
                                                    </div>
                                                ),
                                                rowExpandable: record => true,
                                            }}
                                        />
                                    </>
                                )
                            },
                            {
                                key: '4',
                                label: <span><DatabaseOutlined />过滤设置</span>,
                                children: (
                                    <div style={{ padding: '0 10px' }}>
                                        <div style={{ marginBottom: 20, borderBottom: '1px solid #eee', paddingBottom: 20 }}>
                                            <h3>1. 执行本地过滤</h3>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                                <span>扫描范围:</span>
                                                <Select value={filterTimeRange} style={{ width: 120 }} onChange={setFilterTimeRange}>
                                                    <Option value={6}>6小时内</Option>
                                                    <Option value={12}>12小时内</Option>
                                                    <Option value={24}>24小时内</Option>
                                                    <Option value={48}>48小时内</Option>
                                                </Select>
                                                <Button type="primary" onClick={handleFilterNews} loading={filtering}>
                                                    立即执行过滤
                                                </Button>
                                                <span style={{ color: '#999', fontSize: 13, marginLeft: 10 }}>
                                                    (扫描 "raw" 和 "deduplicated" 状态的新闻，匹配黑名单则标记为 "filtered")
                                                </span>
                                            </div>
                                        </div>

                                        <div>
                                            <h3>2. 黑名单关键词管理</h3>
                                            <div style={{ marginBottom: 16, display: 'flex', gap: 10 }}>
                                                <Select value={newMatchType} style={{ width: 100 }} onChange={setNewMatchType}>
                                                    <Option value="contains">包含</Option>
                                                    <Option value="regex">正则</Option>
                                                </Select>
                                                <Input
                                                    placeholder="输入屏蔽词..."
                                                    style={{ width: 200 }}
                                                    value={newKeyword}
                                                    onChange={e => setNewKeyword(e.target.value)}
                                                    onPressEnter={handleAddKeyword}
                                                />
                                                <Button type="primary" onClick={handleAddKeyword} icon={<PlusOutlined />}>添加</Button>
                                            </div>
                                            <Table
                                                columns={blacklistColumns}
                                                dataSource={blacklistKeywords}
                                                rowKey="id"
                                                pagination={{ pageSize: 10 }}
                                                size="small"
                                            />
                                        </div>


                                        <div style={{ marginTop: 20, paddingTop: 20, borderTop: '1px solid #eee' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                                                <h3>3. 已过滤新闻 (Filtered Results)</h3>
                                                <Button icon={<ReloadOutlined />} onClick={() => fetchFilteredNews(filteredPagination.current)}>刷新</Button>
                                            </div>
                                            <Table
                                                columns={filteredColumns} // Use filtered columns with restore
                                                dataSource={filteredNews}
                                                rowKey="id"
                                                loading={loadingFiltered}
                                                pagination={{
                                                    ...filteredPagination,
                                                    onChange: (page) => fetchFilteredNews(page)
                                                }}
                                                size="small"
                                                expandable={{
                                                    expandedRowRender: record => (
                                                        <div style={{ padding: 16, background: '#fafafa' }}>
                                                            <p><strong>URL:</strong> <a href={record.source_url} target="_blank">{record.source_url}</a></p>
                                                            <p><strong>Flag:</strong> {record.site_importance_flag}</p>
                                                            <div style={{ whiteSpace: 'pre-wrap', maxHeight: 400, overflowY: 'auto' }}>
                                                                {record.content || <span style={{ color: '#ccc' }}>No content available</span>}
                                                            </div>
                                                        </div>
                                                    ),
                                                    rowExpandable: record => true,
                                                }}
                                            />
                                        </div>
                                    </div>
                                )
                            },
                            {
                                key: '5',
                                label: <span><DatabaseOutlined />精选数据</span>,
                                children: (
                                    <>
                                        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
                                            <Space>
                                                <span style={{ fontSize: 14 }}>来源筛选:</span>
                                                <Select
                                                    value={curatedFilterSource}
                                                    style={{ width: 150 }}
                                                    onChange={(val) => {
                                                        setCuratedFilterSource(val);
                                                        fetchCuratedNews(1, val);
                                                    }}
                                                    allowClear
                                                    placeholder="全部来源"
                                                >
                                                    {spiders.map(s => <Option key={s} value={s}>{s}</Option>)}
                                                </Select>
                                                <Button icon={<DownloadOutlined />} onClick={() => handleShowExport('curated')}>导出</Button>
                                            </Space>
                                            <Button icon={<ReloadOutlined />} onClick={() => fetchCuratedNews(curatedPagination.current, curatedFilterSource)}>刷新</Button>
                                        </div>

                                        <Table
                                            columns={curatedColumns}
                                            dataSource={curatedNews}
                                            rowKey="id"
                                            loading={loadingCurated}
                                            pagination={{
                                                ...curatedPagination,
                                                showSizeChanger: false,
                                                onChange: (page) => fetchCuratedNews(page, curatedFilterSource)
                                            }}
                                            expandable={{
                                                expandedRowRender: record => (
                                                    <div style={{ padding: 16, background: '#fafafa' }}>
                                                        <p><strong>URL:</strong> <a href={record.source_url} target="_blank">{record.source_url}</a></p>
                                                        <div style={{ whiteSpace: 'pre-wrap', maxHeight: 400, overflowY: 'auto' }}>
                                                            {record.content || <span style={{ color: '#ccc' }}>No content available</span>}
                                                        </div>
                                                    </div>
                                                ),
                                                rowExpandable: record => true,
                                            }}
                                        />
                                    </>
                                )
                            },
                            {
                                key: '2',
                                label: <span><RobotOutlined />爬虫控制</span>,
                                children: (
                                    <Row gutter={[16, 16]}>
                                        {spiders.map(name => (
                                            <ScraperCard
                                                key={name}
                                                name={name}
                                                status={spiderStatus[name] || {}}
                                                onRun={handleRunSpider}
                                                onCancel={handleStopSpider}
                                                onConfigChange={handleConfigChange}
                                            />
                                        ))}
                                    </Row>
                                )
                            },
                            {
                                key: '6',
                                label: <span><RobotOutlined />通知配置</span>,
                                children: (
                                    <div style={{ padding: '0 10px' }}>
                                        <h3>Telegram 推送配置</h3>
                                        <Card style={{ maxWidth: 600, marginTop: 20 }}>
                                            <div style={{ marginBottom: 16 }}>
                                                <div style={{ marginBottom: 8 }}>Bot Token:</div>
                                                <Input.Password
                                                    value={telegramConfig.bot_token}
                                                    onChange={e => setTelegramConfigState({ ...telegramConfig, bot_token: e.target.value })}
                                                    placeholder="123456789:ABCDefGhIJKlmNoPQRstuVWxyz"
                                                />
                                                <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                                                    从 @BotFather 获取
                                                </div>
                                            </div>

                                            <div style={{ marginBottom: 16 }}>
                                                <div style={{ marginBottom: 8 }}>Chat ID:</div>
                                                <Input
                                                    value={telegramConfig.chat_id}
                                                    onChange={e => setTelegramConfigState({ ...telegramConfig, chat_id: e.target.value })}
                                                    placeholder="@channel_name or -100xxxxxxxx"
                                                />
                                                <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                                                    目标频道/群组 ID，需先将 Bot 拉入并设为管理员
                                                </div>
                                            </div>

                                            <div style={{ marginBottom: 24 }}>
                                                <Checkbox
                                                    checked={telegramConfig.enabled}
                                                    onChange={e => setTelegramConfigState({ ...telegramConfig, enabled: e.target.checked })}
                                                >
                                                    启用自动推送 (仅推送 "精选数据")
                                                </Checkbox>
                                            </div>

                                            <Space>
                                                <Button type="primary" onClick={handleSaveTelegramConfig}>保存配置</Button>
                                                <Button onClick={handleTestTelegramPush}>发送测试消息</Button>
                                            </Space>
                                        </Card>
                                    </div>
                                )
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
