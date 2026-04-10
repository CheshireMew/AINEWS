import React, { lazy, Suspense, useMemo, useState } from 'react';
import { Layout, Button, Card, Row, Col, Statistic, Segmented, Tabs } from 'antd';
import { LogoutOutlined, RobotOutlined, DatabaseOutlined, DownloadOutlined, AppstoreOutlined } from '@ant-design/icons';

import { clearAuthToken } from '../auth/session';
import { CONTENT_KIND } from '../contracts/content';
import { useDashboardData } from '../hooks/useDashboardData';
import DashboardExportModal from '../components/dashboard/DashboardExportModal';

const { Header, Content } = Layout;

const NewsManagementTab = lazy(() => import('../components/dashboard/NewsManagementTab'));
const DuplicateTreeTab = lazy(() => import('../components/dashboard/DuplicateTreeTab'));
const ArchiveTab = lazy(() => import('../components/dashboard/ArchiveTab'));
const ReviewQueueTab = lazy(() => import('../components/dashboard/ReviewQueueTab'));
const DiscardedContentTab = lazy(() => import('../components/dashboard/DiscardedContentTab'));
const SelectedContentTab = lazy(() => import('../components/dashboard/SelectedContentTab'));
const SpiderControlTab = lazy(() => import('../components/dashboard/SpiderControlTab'));
const SystemSettingsTab = lazy(() => import('../components/dashboard/SystemSettingsTab'));
const ExportTab = lazy(() => import('../components/dashboard/ExportTab'));
const BlocklistTab = lazy(() => import('../components/dashboard/BlocklistTab'));

const Dashboard = () => {
    const [activeKey, setActiveKey] = useState('1');
    const [contentKind, setContentKind] = useState(CONTENT_KIND.NEWS);
    const {
        stats,
        spiders,
        spiderStatus,
        rssSources,
        overview,
        manuallyFeatured,
        setManuallyFeatured,
        exportState,
        actions,
    } = useDashboardData(contentKind);

    const handleLogout = () => {
        clearAuthToken();
        window.location.href = '/login';
    };

    const handleTabChange = (key) => {
        setActiveKey(key);
        actions.fetchOverview();
        if (key === '1') {
            actions.fetchStats();
        }
    };

    const tabItems = useMemo(() => [
        {
            key: '1',
            label: <span><DatabaseOutlined />采集池 ({overview.incoming})</span>,
            children: <NewsManagementTab spiders={spiders} onShowExport={exportState.open} contentKind={contentKind} />
        },
        {
            key: '1.5',
            label: <span><AppstoreOutlined />重复对照</span>,
            children: <DuplicateTreeTab spiders={spiders} contentKind={contentKind} />
        },
        {
            key: '3',
            label: <span><DatabaseOutlined />归档池 ({overview.archive})</span>,
            children: <ArchiveTab spiders={spiders} onAddToFeatured={actions.handleAddToFeatured} onShowExport={exportState.open} contentKind={contentKind} />
        },
        {
            key: '4',
            label: <span><DatabaseOutlined />已拦截 ({overview.blocked})</span>,
            children: <BlocklistTab onAddToFeatured={actions.handleAddToFeatured} active={activeKey === '4'} contentKind={contentKind} />
        },
        {
            key: '5',
            label: <span><DatabaseOutlined />待审核 ({overview.review})</span>,
            children: <ReviewQueueTab spiders={spiders} onAddToFeatured={actions.handleAddToFeatured} onShowExport={exportState.open} active={activeKey === '5'} contentKind={contentKind} />
        },
        {
            key: '8',
            label: <span><RobotOutlined />已舍弃 ({overview.discarded})</span>,
            children: <DiscardedContentTab onAddToFeatured={actions.handleAddToFeatured} contentKind={contentKind} />
        },
        {
            key: '9',
            label: <span><DatabaseOutlined />已选入 ({overview.selected})</span>,
            children: <SelectedContentTab spiders={spiders} onAddToFeatured={actions.handleAddToFeatured} onShowExport={exportState.open} contentKind={contentKind} />
        },
        {
            key: '2',
            label: <span><RobotOutlined />爬虫控制</span>,
            children: (
                <SpiderControlTab
                    spiders={spiders}
                    spiderStatus={spiderStatus}
                    rssSources={rssSources}
                    onRun={actions.handleRunSpider}
                    onCancel={actions.handleStopSpider}
                    onConfigChange={actions.handleConfigChange}
                    onCreateRssSource={actions.handleCreateRssSource}
                    onUpdateRssSource={actions.handleUpdateRssSource}
                    onDeleteRssSource={actions.handleDeleteRssSource}
                    contentKind={contentKind}
                />
            )
        },
        {
            key: '6',
            label: <span><RobotOutlined />系统配置</span>,
            children: <SystemSettingsTab />
        },
        {
            key: '7',
            label: <span><DownloadOutlined />结果输出</span>,
            children: <ExportTab manuallyFeatured={manuallyFeatured} setManuallyFeatured={setManuallyFeatured} contentKind={contentKind} />
        }
    ], [
        activeKey,
        actions,
        contentKind,
        exportState.open,
        manuallyFeatured,
        overview,
        setManuallyFeatured,
        spiderStatus,
        rssSources,
        spiders,
    ]);

    const activeTabItem = tabItems.find((item) => item.key === activeKey) ?? tabItems[0];

    return (
        <Layout className="layout" style={{ minHeight: '100vh' }}>
            <Header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ color: 'white', fontSize: '20px', fontWeight: 'bold' }}>AINews Admin</div>
                <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                    <Segmented
                        options={[
                            { label: '⚡️ 快讯', value: CONTENT_KIND.NEWS },
                            { label: '📄 文章', value: CONTENT_KIND.ARTICLE }
                        ]}
                        value={contentKind}
                        onChange={setContentKind}
                    />
                    <Button type="primary" danger icon={<LogoutOutlined />} onClick={handleLogout}>
                        退出
                    </Button>
                </div>
            </Header>
            <Content style={{ padding: '20px 50px' }}>
                <div style={{ marginBottom: 20 }}>
                    <Row gutter={[16, 16]}>
                        {stats.map((item) => (
                            <Col span={4} xl={3} key={item.source}>
                                <Card size="small">
                                    <Statistic
                                        title={item.source}
                                        value={item.count}
                                        formatter={(value) => <span style={{ color: '#3f8600' }}>{value}</span>}
                                        prefix={<DatabaseOutlined />}
                                    />
                                </Card>
                            </Col>
                        ))}
                    </Row>
                </div>

                <div style={{ background: '#fff', padding: 24, minHeight: 280 }}>
                    <Tabs
                        destroyOnHidden
                        activeKey={activeKey}
                        onChange={handleTabChange}
                        items={tabItems.map((item) => ({
                            key: item.key,
                            label: item.label,
                            children: item.key === activeTabItem.key ? <Suspense fallback={null}>{item.children}</Suspense> : null,
                        }))}
                    />
                </div>
            </Content>

            <DashboardExportModal exportState={exportState} />
        </Layout>
    );
};

export default Dashboard;
