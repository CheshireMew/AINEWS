import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { Card, Select, Button, Space, message, DatePicker, Table, Tag } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import { getExportNews, sendNewsToTelegram, triggerDailyPush } from '../../api';
import TimeRangeSelect from './TimeRangeSelect';

const { Option } = Select;

/**
 * 新闻输出Tab组件
 * 用于加载、筛选和导出AI评分的新闻
 */
const ExportTab = ({ manuallyFeatured, setManuallyFeatured }) => {
    // 筛选条件状态
    const [exportTimeRange, setExportTimeRange] = useState(24); // 24小时
    const [exportMinScore, setExportMinScore] = useState(6); // 最低6分

    // 数据状态
    const [exportNews, setExportNews] = useState([]);
    const [newsExportLoading, setNewsExportLoading] = useState(false);
    const [selectedNewsIds, setSelectedNewsIds] = useState([]);
    const [sendingToTg, setSendingToTg] = useState(false);

    /**
     * 加载新闻
     */
    const handleLoadNews = async () => {
        try {
            setNewsExportLoading(true);
            // 清空手动加精列表
            setManuallyFeatured([]);
            const res = await getExportNews(exportTimeRange, exportMinScore);
            setExportNews(res.data.news || []);
            setSelectedNewsIds([]);
            message.success(`加载了 ${res.data.news?.length || 0} 条新闻`);
        } catch (e) {
            message.error('加载失败: ' + (e.response?.data?.detail || e.message));
        } finally {
            setNewsExportLoading(false);
        }
    };

    /**
     * 复制为纯文本
     */
    const handleCopyPlainText = () => {
        const selected = exportNews.filter(n => selectedNewsIds.includes(n.id));
        if (selected.length === 0) {
            message.warning('请先选择要复制的新闻');
            return;
        }
        const text = selected.map(n => {
            if (n.content) {
                return `${n.title}\n\n${n.content}`;
            }
            return n.title;
        }).join('\n\n---\n\n');
        navigator.clipboard.writeText(text);
        message.success(`已复制 ${selected.length} 条新闻（含标题和内容）`);
    };

    /**
     * 复制为Markdown格式
     */
    const handleCopyMarkdown = () => {
        const selected = exportNews.filter(n => selectedNewsIds.includes(n.id));
        if (selected.length === 0) {
            message.warning('请先选择要复制的新闻');
            return;
        }
        const text = selected.map(n => {
            const content = n.content ? n.content.replace(/\n/g, '\n>\n> ') : 'No Content';
            return `### [${n.title}](${n.source_url})\n\n> ${content}\n\n---`;
        }).join('\n\n');
        navigator.clipboard.writeText(text);
        message.success(`已复制 ${selected.length} 条新闻`);
    };

    /**
     * 复制为TG格式（HTML超链接）
     */
    const handleCopyTG = async () => {
        const selected = exportNews.filter(n => selectedNewsIds.includes(n.id));
        if (selected.length === 0) {
            message.warning('请先选择要复制的新闻');
            return;
        }

        // TG Footer constants - Simple HTML fragment
        const footerHtml = `
<br><br>
<a href="https://0xcheshire.gitbook.io/web3/">币圈新人手册</a><br>
注册交易所 <a href="https://binance.com/join?ref=SRXT5KUM">币安</a> <a href="https://okx.com/join/A999998">欧易</a><br>
Web3钱包 <a href="https://web3.binance.com/referral?ref=RP3AEJ2M">币安</a> <a href="https://web3.okx.com/ul/joindex?ref=1234567">OKX</a> <a href="https://link.metamask.io/rewards?referral=36P4HH">小狐狸（刷分）</a>`;

        const footerText = `
币圈新人手册 https://0xcheshire.gitbook.io/web3/
注册交易所 币安 https://binance.com/join?ref=SRXT5KUM 欧易 https://okx.com/join/A999998  
Web3钱包 币安 https://web3.binance.com/referral?ref=RP3AEJ2M OKX https://web3.okx.com/ul/joindex?ref=1234567 小狐狸（刷分） https://link.metamask.io/rewards?referral=36P4HH`;

        // 构建HTML内容，Telegram支持的格式
        // 既然用户提供的"老代码"好用，我们回归最简模式：只用<a>和<br>
        const htmlLinks = selected
            .map(n => `<a href="${n.source_url}">${escapeHtml(n.title)}</a>`)
            .join('<br><br>');

        // 拼接 HTML (不带 DOCTYPE/html/body，因为用户反馈这样好用)
        const htmlContent = htmlLinks + footerHtml;

        // 纯文本fallback - 包含链接
        const plainText = selected
            .map(n => `${n.title}\n${n.source_url}`)
            .join('\n\n') + '\n' + footerText;

        try {
            // 写入剪贴板
            const htmlBlob = new Blob([htmlContent], { type: 'text/html' });
            const textBlob = new Blob([plainText], { type: 'text/plain' });

            await navigator.clipboard.write([
                new ClipboardItem({
                    'text/html': htmlBlob,
                    'text/plain': textBlob
                })
            ]);
            message.success(`已复制 ${selected.length} 条，粘贴到Telegram即为蓝色链接`);
        } catch (err) {
            console.error('Copy failed:', err);
            message.error('复制失败，请重试');
        }
    };

    // HTML转义函数
    const escapeHtml = (text) => {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };

    /**
     * 发送到Telegram
     */
    const handleSendToTelegram = async () => {
        const selected = exportNews.filter(n => selectedNewsIds.includes(n.id));
        if (selected.length === 0) {
            message.warning('请先选择要发送的新闻');
            return;
        }

        try {
            setSendingToTg(true);
            const response = await sendNewsToTelegram(selectedNewsIds);
            message.success(response.message || `成功发送${selected.length}条新闻到Telegram`);
        } catch (err) {
            console.error('Send to Telegram failed:', err);
            message.error(err.message || '发送失败，请检查Telegram配置');
        } finally {
            setSendingToTg(false);
        }
    };

    /**
     * 全选/取消全选
     */
    const handleToggleSelectAll = () => {
        if (selectedNewsIds.length === exportNews.length) {
            setSelectedNewsIds([]);
        } else {
            setSelectedNewsIds(exportNews.map(n => n.id));
        }
    };

    /**
     * 反选
     */
    const handleInvertSelection = () => {
        const allIds = exportNews.map(n => n.id);
        const newSelected = allIds.filter(id => !selectedNewsIds.includes(id));
        setSelectedNewsIds(newSelected);
    };

    // 表格列定义
    const columns = [
        {
            title: '评分',
            dataIndex: 'score',
            width: 120,
            render: (score, record) => (
                <Space>
                    {record.isFeatured && <Tag color="gold">⭐手动</Tag>}
                    {score && <Tag color={score >= 8 ? 'green' : score >= 7 ? 'blue' : 'default'}>{score}分</Tag>}
                </Space>
            )
        },
        {
            title: '标题',
            dataIndex: 'title',
            render: (text, record) => <a href={record.source_url} target="_blank" rel="noopener noreferrer">{text}</a>
        },
        {
            title: '来源',
            dataIndex: 'source_site',
            width: 100,
            render: (text) => <Tag>{text}</Tag>
        },
        {
            title: 'AI标签',
            dataIndex: 'ai_explanation',
            width: 200,
            ellipsis: true,
            render: (text) => {
                if (!text) return '-';
                const parts = text.split(' - ');
                if (parts.length < 2) return text;
                const reason = parts[1]?.split('#')[0]?.trim() || '';
                return <span style={{ fontSize: 12, color: '#666' }}>{reason}</span>;
            }
        }
    ];

    return (
        <div style={{ padding: '0 10px' }}>
            {/* 筛选条件 */}
            <Card style={{ marginBottom: 16 }}>
                <Space size="large">
                    <div>
                        <span style={{ marginRight: 8 }}>时间范围:</span>
                        <TimeRangeSelect value={exportTimeRange} onChange={setExportTimeRange} />
                    </div>
                    <div>
                        <span style={{ marginRight: 8 }}>最低评分:</span>
                        <Select value={exportMinScore} style={{ width: 100 }} onChange={setExportMinScore}>
                            <Option value={4}>≥ 4分</Option>
                            <Option value={5}>≥ 5分</Option>
                            <Option value={6}>≥ 6分</Option>
                            <Option value={7}>≥ 7分</Option>
                            <Option value={8}>≥ 8分</Option>
                            <Option value={9}>≥ 9分</Option>
                        </Select>
                    </div>
                    <Button
                        type="primary"
                        onClick={handleLoadNews}
                        loading={newsExportLoading}
                    >
                        加载新闻
                    </Button>
                    <Button
                        onClick={async () => {
                            try {
                                message.loading('正在触发日报推送...', 1);
                                const res = await triggerDailyPush();
                                if (res.data && res.data.status === 'success') {
                                    message.success(`推送成功: 已发送 ${res.data.count} 条精选新闻`);
                                } else if (res.data && res.data.status === 'skipped') {
                                    message.warning(`推送跳过: ${res.data.message}`);
                                } else {
                                    message.warning('推送完成，请检查TG消息');
                                }
                            } catch (e) {
                                message.error('触发失败: ' + (e.response?.data?.message || e.message));
                            }
                        }}
                    >
                        推送精选日报 (20:00)
                    </Button>
                </Space>
            </Card>

            {/* 操作按钮 */}
            {exportNews.length > 0 && (
                <Card style={{ marginBottom: 16 }}>
                    <div style={{ marginBottom: 12 }}>
                        <Tag color="blue">已选 {selectedNewsIds.length}/{exportNews.length} 条</Tag>
                    </div>
                    <Space wrap>
                        <Button onClick={handleToggleSelectAll}>
                            {selectedNewsIds.length === exportNews.length ? '取消全选' : '全选'}
                        </Button>
                        <Button onClick={handleInvertSelection}>反选</Button>
                        <Button onClick={() => setSelectedNewsIds([])}>清空</Button>
                        <div style={{ borderLeft: '1px solid #d9d9d9', height: 32, margin: '0 8px' }} />
                        <Button type="primary" onClick={handleCopyPlainText}>复制为纯文本</Button>
                        <Button onClick={handleCopyMarkdown}>Markdown格式</Button>
                        <Button onClick={handleCopyTG}>TG格式</Button>
                        <Button
                            icon={<SendOutlined />}
                            onClick={handleSendToTelegram}
                            loading={sendingToTg}
                        >
                            发送到TG
                        </Button>

                    </Space>
                </Card>
            )}

            {/* 新闻列表 */}
            <Table
                dataSource={[
                    ...manuallyFeatured.map(n => ({ ...n, isFeatured: true })),
                    ...exportNews
                ]}
                rowKey="id"
                loading={newsExportLoading}
                pagination={false}
                rowSelection={{
                    selectedRowKeys: selectedNewsIds,
                    onChange: (selectedKeys) => setSelectedNewsIds(selectedKeys)
                }}
                expandable={{
                    expandedRowRender: (record) => (
                        <div style={{ padding: '12px 24px', backgroundColor: '#fafafa' }}>
                            <p style={{ margin: 0, whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
                                {record.content || '暂无内容'}
                            </p>
                        </div>
                    ),
                    rowExpandable: (record) => !!record.content
                }}
                columns={columns}
            />
        </div>
    );
};

ExportTab.propTypes = {
    manuallyFeatured: PropTypes.arrayOf(PropTypes.object)
};

export default ExportTab;
