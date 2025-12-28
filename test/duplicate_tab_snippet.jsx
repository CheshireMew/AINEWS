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

// ... [其他函数保持不变，这里继续写]
