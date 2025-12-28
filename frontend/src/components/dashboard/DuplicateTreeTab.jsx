import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Table, Button, Tag, message, Divider, Pagination, Input, Card, Row, Col } from 'antd';
import { getNews, deleteNews, checkNewsSimilarity } from '../../api';
import NewsToolbar from './NewsToolbar';
import usePaginationConfig from '../common/usePaginationConfig';

/**
 * 重复对照Tab组件
 * 显示所有原始新闻：有重复的（可展开）+ 独立的（无重复）
 */
const DuplicateTreeTab = ({ spiders, onShowExport }) => {
    const [groups, setGroups] = useState([]);
    const [loading, setLoading] = useState(false);
    const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });
    const [filterSource, setFilterSource] = useState(undefined);
    const [filterKeyword, setFilterKeyword] = useState('');
    const [expandedGroups, setExpandedGroups] = useState(new Set());

    // 相似度检测工具状态
    const [newsId1, setNewsId1] = useState('');
    const [newsId2, setNewsId2] = useState('');
    const [similarityResult, setSimilarityResult] = useState(null);
    const [checkingLoading, setCheckingLoading] = useState(false);

    const { getPaginationConfig } = usePaginationConfig(20);

    /**
     * 切换组的展开/折叠状态
     */
    const toggleGroup = (groupIndex) => {
        const newExpanded = new Set(expandedGroups);
        if (newExpanded.has(groupIndex)) {
            newExpanded.delete(groupIndex);
        } else {
            newExpanded.add(groupIndex);
        }
        setExpandedGroups(newExpanded);
    };

    /**
     * 将新闻数据分类显示
     * 返回所有原始新闻：1) 有重复的  2) 独立的
     */
    const groupBySimilarity = (newsList) => {
        const newsMap = {};
        newsList.forEach(item => {
            newsMap[item.id] = item;
        });

        // 收集duplicates并按master分组
        const duplicates = newsList.filter(item => item.duplicate_of);
        const masterGroups = {};

        duplicates.forEach(dup => {
            const masterId = dup.duplicate_of;
            if (newsMap[masterId]) {
                if (!masterGroups[masterId]) {
                    masterGroups[masterId] = {
                        master: newsMap[masterId],
                        duplicates: [],
                        type: 'group'
                    };
                }
                masterGroups[masterId].duplicates.push(dup);
            }
        });

        // 获取所有原始新闻，分为有重复和独立的
        const allMasters = newsList.filter(item => !item.duplicate_of);
        const result = allMasters.map(master => {
            if (masterGroups[master.id]) {
                return masterGroups[master.id];
            } else {
                return {
                    master: master,
                    duplicates: [],
                    type: 'independent'
                };
            }
        });

        return result;
    };

    /**
     * 获取新闻数据并分组
     */
    const fetchNews = async (page = 1, pageSize = pagination.pageSize, source = filterSource, keyword = filterKeyword) => {
        setLoading(true);
        try {
            const res = await getNews(1, 10000, source, null, keyword);
            const similarityGroups = groupBySimilarity(res.data.data);

            setGroups(similarityGroups);
            setPagination({
                current: page,
                pageSize: pageSize,
                total: similarityGroups.length
            });
        } catch (e) {
            console.error("Fetch groups failed", e);
        } finally {
            setLoading(false);
        }
    };

    /**
     * 删除新闻
     */
    const handleDeleteNews = async (id) => {
        try {
            await deleteNews(id);
            message.success('删除成功');
            fetchNews(pagination.current, pagination.pageSize, filterSource, filterKeyword);
        } catch (e) {
            message.error('删除失败');
        }
    };

    /**
     * 检测两条新闻的相似度
     */
    const handleCheckSimilarity = async () => {
        if (!newsId1 || !newsId2) {
            message.warning('请输入两个新闻ID');
            return;
        }

        setCheckingLoading(true);
        try {
            const res = await checkNewsSimilarity(parseInt(newsId1), parseInt(newsId2));
            setSimilarityResult(res.data);
            message.success('检测完成');
        } catch (e) {
            message.error('检测失败: ' + (e.response?.data?.detail || e.message));
            setSimilarityResult(null);
        } finally {
            setCheckingLoading(false);
        }
    };

    useEffect(() => {
        fetchNews(1, pagination.pageSize, filterSource, filterKeyword);
    }, []);

    // 计算当前页的分组
    const currentPageGroups = groups.slice(
        (pagination.current - 1) * pagination.pageSize,
        pagination.current * pagination.pageSize
    );

    // 统计
    const groupCount = groups.filter(g => g.type === 'group').length;
    const independentCount = groups.filter(g => g.type === 'independent').length;

    return (
        <>
            <NewsToolbar
                onSearch={(val) => {
                    setFilterKeyword(val);
                    fetchNews(1, pagination.pageSize, filterSource, val);
                }}
                spiders={spiders}
                selectedSource={filterSource}
                onSourceChange={(val) => {
                    setFilterSource(val);
                    fetchNews(1, pagination.pageSize, val, filterKeyword);
                }}
                onExport={() => onShowExport && onShowExport('tree')}
                onRefresh={() => fetchNews(pagination.current, pagination.pageSize, filterSource, filterKeyword)}
                loading={loading}
            />

            <div style={{ padding: '16px' }}>
                {/* 🆕 相似度检测工具 */}
                <Card title="🔍 相似度检测工具" size="small" style={{ marginBottom: '16px' }}>
                    <Row gutter={[8, 8]} align="middle">
                        <Col><Input placeholder="新闻ID 1" value={newsId1} onChange={(e) => setNewsId1(e.target.value)} style={{ width: '120px' }} /></Col>
                        <Col><Input placeholder="新闻ID 2" value={newsId2} onChange={(e) => setNewsId2(e.target.value)} style={{ width: '120px' }} /></Col>
                        <Col><Button type="primary" onClick={handleCheckSimilarity} loading={checkingLoading}>检测相似度</Button></Col>
                        {similarityResult && (
                            <Col flex="auto">
                                <div style={{ background: similarityResult.is_duplicate ? '#f6ffed' : '#fff7e6', padding: '8px 12px', borderRadius: '4px' }}>
                                    相似度: {(similarityResult.similarity * 100).toFixed(2)}% | {similarityResult.is_duplicate ? '✅ 判定为重复' : '❌ 未达阈值'}
                                </div>
                            </Col>
                        )}
                    </Row>
                </Card>

                {/* 统计提示 */}
                {!loading && groups.length > 0 && (
                    <div style={{
                        background: '#e6f7ff',
                        border: '1px solid #91d5ff',
                        borderRadius: '4px',
                        padding: '12px 16px',
                        marginBottom: '16px'
                    }}>
                        <div style={{ fontSize: '14px', color: '#1890ff', marginBottom: '4px' }}>
                            ℹ️ 显示所有 {groups.length} 条原始新闻
                        </div>
                        <div style={{ fontSize: '13px', color: '#666', display: 'flex', gap: '24px' }}>
                            <span>▶ 有重复: {groupCount} 条（可展开查看重复项）</span>
                            <span>✅ 独立: {independentCount} 条（无重复）</span>
                        </div>
                    </div>
                )}

                {loading ? (
                    <div style={{ textAlign: 'center', padding: '50px' }}>加载中...</div>
                ) : currentPageGroups.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '50px', color: '#999' }}>
                        ✅ 没有原始新闻
                    </div>
                ) : (
                    currentPageGroups.map((group, groupIndex) => {
                        const globalIndex = (pagination.current - 1) * pagination.pageSize + groupIndex;
                        const isExpanded = expandedGroups.has(globalIndex);
                        const isGroup = group.type === 'group';

                        return (
                            <div key={groupIndex} style={{ marginBottom: '16px', border: '1px solid #f0f0f0', borderRadius: '8px', overflow: 'hidden' }}>
                                {/* Master新闻 */}
                                <div
                                    style={{
                                        background: isGroup ? '#fafafa' : '#f0f9ff',
                                        padding: '12px 16px',
                                        borderBottom: (isGroup && isExpanded) ? '2px solid #1890ff' : 'none',
                                        cursor: isGroup ? 'pointer' : 'default',
                                        transition: 'background 0.2s'
                                    }}
                                    onClick={isGroup ? () => toggleGroup(globalIndex) : undefined}
                                    onMouseEnter={isGroup ? (e) => e.currentTarget.style.background = '#f0f0f0' : undefined}
                                    onMouseLeave={isGroup ? (e) => e.currentTarget.style.background = '#fafafa' : undefined}
                                >
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div style={{ flex: 1, display: 'flex', alignItems: 'center' }}>
                                            {isGroup ? (
                                                <>
                                                    <span style={{ marginRight: 8, fontSize: '14px', color: '#999' }}>
                                                        {isExpanded ? '▼' : '▶'}
                                                    </span>
                                                    <Tag color="blue" style={{ marginRight: 8 }}>原始 ID:{group.master.id}</Tag>
                                                    <Tag color="orange">{group.duplicates.length}条重复</Tag>
                                                </>
                                            ) : (
                                                <>
                                                    <span style={{ marginRight: 8, fontSize: '14px', color: '#52c41a' }}>✅</span>
                                                    <Tag color="green" style={{ marginRight: 8 }}>独立 ID:{group.master.id}</Tag>
                                                </>
                                            )}
                                            <a
                                                href={group.master.source_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                style={{ fontWeight: 'bold', fontSize: '14px', marginLeft: '8px' }}
                                                onClick={(e) => e.stopPropagation()}
                                            >
                                                {group.master.title}
                                            </a>
                                        </div>
                                        <div>
                                            <Tag>{group.master.source_site}</Tag>
                                            <span style={{ marginLeft: 8, color: '#999', fontSize: '12px' }}>
                                                {new Date(group.master.published_at).toLocaleString()}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                {/* Duplicate新闻列表 */}
                                {isGroup && isExpanded && group.duplicates.map((dup, dupIndex) => (
                                    <div key={dupIndex} style={{ padding: '12px 16px 12px 40px', borderBottom: dupIndex < group.duplicates.length - 1 ? '1px solid #f0f0f0' : 'none', background: '#fff' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            <div style={{ flex: 1 }}>
                                                <Tag color="volcano" style={{ marginRight: 8 }}>重复 ID:{dup.id}</Tag>
                                                <a href={dup.source_url} target="_blank" rel="noopener noreferrer" style={{ fontSize: '13px' }}>
                                                    {dup.title}
                                                </a>
                                            </div>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                                <Tag>{dup.source_site}</Tag>
                                                <span style={{ color: '#999', fontSize: '12px', minWidth: '140px' }}>
                                                    {new Date(dup.published_at).toLocaleString()}
                                                </span>
                                                <Button
                                                    type="link"
                                                    danger
                                                    size="small"
                                                    onClick={() => handleDeleteNews(dup.id)}
                                                >
                                                    删除
                                                </Button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        );
                    })
                )}

                {/* 分页 */}
                {groups.length > 0 && (
                    <div style={{ marginTop: '20px', textAlign: 'right' }}>
                        <span style={{ marginRight: '16px' }}>共 {groups.length} 条原始新闻</span>
                        <Pagination
                            {...getPaginationConfig(
                                pagination,
                                (page, pageSize) => setPagination({ ...pagination, current: page, pageSize }),
                                (page, pageSize) => setPagination({ ...pagination, current: page, pageSize })
                            )}
                        />
                    </div>
                )}
            </div>
        </>
    );
};

DuplicateTreeTab.propTypes = {
    spiders: PropTypes.arrayOf(PropTypes.shape({
        name: PropTypes.string,
        url: PropTypes.string
    })),
    onShowExport: PropTypes.func
};

export default DuplicateTreeTab;
