import React, { useState, useEffect, useRef } from 'react';
import { CaretDown, Lightning, MagnifyingGlass, Moon, Sun, ArrowUp, Fire } from '@phosphor-icons/react';
import { FaHome, FaTelegramPlane, FaTwitter, FaBlog, FaGithub, FaBook } from 'react-icons/fa';
import { SiBinance } from 'react-icons/si';
import { API_BASE_URL } from '../config';

// OKX Logo 组件
const OKXLogo = ({ className }) => (
    <svg viewBox="0 0 24 24" className={className} fill="currentColor" width="1em" height="1em">
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="13" y="3" width="7" height="7" rx="1.5" />
        <rect x="8" y="8" width="7" height="7" rx="1.5" />
        <rect x="3" y="13" width="7" height="7" rx="1.5" />
        <rect x="13" y="13" width="7" height="7" rx="1.5" />
    </svg>
);

export default function NewsFeed() {
    // 状态管理
    const [activeTab, setActiveTab] = useState('article');
    const [articles, setArticles] = useState([]);
    const [newsList, setNewsList] = useState([]);
    const [dailyArticles, setDailyArticles] = useState([]);
    const [dailyNews, setDailyNews] = useState([]);
    const [loading, setLoading] = useState(false);

    // 分页状态
    const [articlePage, setArticlePage] = useState(1);
    const [newsPage, setNewsPage] = useState(1);
    const [hasMoreArticles, setHasMoreArticles] = useState(true);
    const [hasMoreNews, setHasMoreNews] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const MAX_PAGES = 50; // 增加最大加载页数，避免用户感觉中断
    const [searchQuery, setSearchQuery] = useState('');
    const [debouncedSearchQuery, setDebouncedSearchQuery] = useState('');
    const [selectedReport, setSelectedReport] = useState(null);
    const [menuOpen, setMenuOpen] = useState(false);

    // 使用 ref 保存最新的状态，避免定时器闭包问题
    const activeTabRef = useRef(activeTab);
    const articlesRef = useRef(articles);
    const newsListRef = useRef(newsList);

    // 更新 ref
    useEffect(() => {
        activeTabRef.current = activeTab;
    }, [activeTab]);

    useEffect(() => {
        articlesRef.current = articles;
    }, [articles]);

    useEffect(() => {
        newsListRef.current = newsList;
    }, [newsList]);

    // 暗黑模式状态
    const [darkMode, setDarkMode] = useState(() => {
        if (typeof window !== 'undefined') {
            return localStorage.getItem('theme') === 'dark' ||
                (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches);
        }
        return false;
    });

    // 监听暗黑模式变化
    useEffect(() => {
        if (darkMode) {
            document.documentElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        }
    }, [darkMode]);

    // 点击外部关闭菜单
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (menuOpen && !event.target.closest('.menu-dropdown')) {
                setMenuOpen(false);
            }
        };

        document.addEventListener('click', handleClickOutside);
        return () => document.removeEventListener('click', handleClickOutside);
    }, [menuOpen]);

    // Search Debounce
    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedSearchQuery(searchQuery);
        }, 800); // 延迟 800ms 等待用户输入完成

        return () => clearTimeout(timer);
    }, [searchQuery]);

    // 监听滚动加载
    useEffect(() => {
        const handleScroll = () => {
            // 当滚动到距离底部 500px 时触发加载 (提前加载，防止等待)
            if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 500) {
                if (!loadingMore && !loading) {
                    loadMore();
                }
            }
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, [loadingMore, loading, activeTab, hasMoreArticles, hasMoreNews, articlePage, newsPage]);

    // 初始化加载
    useEffect(() => {
        if (activeTab === 'article') {
            // 重置文章分页并重新加载
            if (articles.length === 0) {
                setArticlePage(1);
                setHasMoreArticles(true);
                fetchArticles(1, false);
            }
        } else if (activeTab === 'daily-article') {
            if (dailyArticles.length === 0) {
                fetchDailyArticles();
            }
        } else if (activeTab === 'daily-news') {
            if (dailyNews.length === 0) {
                fetchDailyNews();
            }
        }
    }, [activeTab]);

    // 初始化加载快讯
    useEffect(() => {
        setNewsPage(1);
        setHasMoreNews(true);
        fetchNews(1, false);
    }, []);

    // 自动检查并刷新新内容（每5分钟）
    useEffect(() => {
        const checkAndRefresh = async () => {
            try {
                // 使用 ref 获取最新值
                const currentTab = activeTabRef.current;
                const currentArticles = articlesRef.current;
                const currentNewsList = newsListRef.current;

                console.log(`⏰ 执行定时检查 - 当前Tab: ${currentTab}, 文章数: ${currentArticles.length}, 快讯数: ${currentNewsList.length}`);

                // 同时检查文章和快讯，不管当前在哪个Tab

                // 检查文章是否有新内容
                if (currentArticles.length > 0) {
                    console.log('📰 检查文章更新...');
                    // 获取最新的20条文章
                    const response = await fetch(`${API_BASE_URL}/api/public/articles?limit=20&offset=0`);
                    const data = await response.json();
                    console.log('📥 获取到的数据:', data.success ? `${data.data?.items?.length || 0}条` : '失败');

                    if (data.success && data.data && data.data.items && data.data.items.length > 0) {
                        // 找出所有新文章（ID不在当前列表中的）
                        const currentIds = new Set(currentArticles.map(a => a.id));
                        const newArticles = data.data.items.filter(item => !currentIds.has(item.id));

                        console.log(`🔍 检测结果: 当前列表有${currentArticles.length}篇, 获取到${data.data.items.length}篇, 其中${newArticles.length}篇是新的`);
                        console.log('📋 当前第一篇ID:', currentArticles[0]?.id, '最新第一篇ID:', data.data.items[0]?.id);

                        if (newArticles.length > 0) {
                            // 将新文章添加到列表顶部
                            setArticles(prev => [...newArticles, ...prev]);
                            console.log(`🔄 自动刷新：添加了 ${newArticles.length} 篇新文章`);
                        } else {
                            console.log('✅ 没有新文章');
                        }
                    }
                }

                // 检查快讯是否有新内容
                if (currentNewsList.length > 0) {
                    console.log('⚡ 检查快讯更新...');
                    // 获取最新的20条快讯
                    const response = await fetch(`${API_BASE_URL}/api/public/news?limit=20&offset=0`);
                    const data = await response.json();
                    console.log('📥 获取到的数据:', data.success ? `${data.data?.items?.length || 0}条` : '失败');

                    if (data.success && data.data && data.data.items && data.data.items.length > 0) {
                        // 找出所有新快讯
                        const currentIds = new Set(currentNewsList.map(n => n.id));
                        const newNews = data.data.items.filter(item => !currentIds.has(item.id));

                        console.log(`🔍 检测结果: 当前列表有${currentNewsList.length}条, 获取到${data.data.items.length}条, 其中${newNews.length}条是新的`);
                        console.log('📋 当前第一条ID:', currentNewsList[0]?.id, '最新第一条ID:', data.data.items[0]?.id);

                        if (newNews.length > 0) {
                            // 将新快讯添加到列表顶部
                            setNewsList(prev => [...newNews, ...prev]);
                            console.log(`🔄 自动刷新：添加了 ${newNews.length} 条新快讯`);
                        } else {
                            console.log('✅ 没有新快讯');
                        }
                    }
                }
            } catch (error) {
                console.error('检查新内容失败:', error);
            }
        };

        // 立即运行一次检查（仅用于测试）
        console.log('✅ 自动刷新定时器已启动，每1分钟检查一次');

        // 每1分钟检查一次（60000ms），方便测试
        const interval = setInterval(checkAndRefresh, 60000);

        return () => {
            console.log('⏹️ 自动刷新定时器已清除');
            clearInterval(interval);
        };
    }, []); // 空依赖数组，避免重复创建定时器

    // 刷新页面以显示新内容
    const refreshContent = () => {
        setHasNewContent(false);
        setNewContentCount(0);

        if (activeTab === 'article') {
            setArticlePage(1);
            setHasMoreArticles(true);
            fetchArticles(1, false);
        } else {
            setNewsPage(1);
            setHasMoreNews(true);
            fetchNews(1, false);
        }

        // 滚动到顶部
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    // 加载更多
    const loadMore = async () => {
        // 如果在前5页（预加载阶段），不要手动触发加载，防止重复
        const isPreloadingPhase = (activeTab === 'article' && articlePage < 5) || (newsPage < 5);

        if (loadingMore || isPreloadingPhase) return;

        setLoadingMore(true);
        const promises = [];

        // 加载更多文章
        if (activeTab === 'article' && hasMoreArticles && articlePage < MAX_PAGES) {
            promises.push(fetchArticles(articlePage + 1, true));
        }

        // 加载更多快讯
        if (hasMoreNews && newsPage < MAX_PAGES) {
            promises.push(fetchNews(newsPage + 1, true));
        }

        await Promise.all(promises);
        setLoadingMore(false);
    };

    // 获取文章列表
    const fetchArticles = async (page = 1, isLoadMore = false) => {
        // 静默预加载：第2-5页不显示底部加载指示器
        const isSilentPreload = page > 1 && page <= 5;

        if (!isLoadMore) {
            setLoading(true);
        } else if (!isSilentPreload) {
            setLoadingMore(true);
        }

        try {
            const limit = 20; // 调整为每页20条，5页共100条
            const offset = (page - 1) * limit;
            const response = await fetch(`${API_BASE_URL}/api/public/articles?limit=${limit}&offset=${offset}`);
            const data = await response.json();

            if (data.success && data.data) {
                const newItems = data.data.items || [];
                if (isLoadMore) {
                    setArticles(prev => {
                        const existingIds = new Set(prev.map(i => i.id));
                        const uniqueNewItems = newItems.filter(i => !existingIds.has(i.id));
                        return [...prev, ...uniqueNewItems];
                    });
                } else {
                    setArticles(newItems);
                }

                // 更新分页状态
                setArticlePage(page);
                setHasMoreArticles(newItems.length === limit);

                // 预加载逻辑：如果是前5页，且还有更多数据，自动加载下一页
                if (page < 5 && newItems.length === limit) {
                    // 延迟 800ms 启动下一页加载，确保当前页面渲染完成
                    setTimeout(() => {
                        fetchArticles(page + 1, true);
                    }, 800);
                }
            }
        } catch (error) {
            console.error('获取文章失败:', error);
        } finally {
            if (!isLoadMore) setLoading(false);
            if (isLoadMore && !isSilentPreload) setLoadingMore(false);
        }
    };

    // 获取快讯列表
    const fetchNews = async (page = 1, isLoadMore = false) => {
        const isSilentPreload = page > 1 && page <= 5;

        try {
            const limit = 20; // 保持每页20条
            const offset = (page - 1) * limit;
            const response = await fetch(`${API_BASE_URL}/api/public/news?limit=${limit}&offset=${offset}`);
            const data = await response.json();

            if (data.success && data.data) {
                const newItems = data.data.items || [];
                if (isLoadMore) {
                    setNewsList(prev => {
                        const existingIds = new Set(prev.map(i => i.id));
                        const uniqueNewItems = newItems.filter(i => !existingIds.has(i.id));
                        return [...prev, ...uniqueNewItems];
                    });
                } else {
                    setNewsList(newItems);
                }

                // 更新分页状态
                setNewsPage(page);
                setHasMoreNews(newItems.length === limit);

                // 预加载逻辑：如果是前5页，且还有更多数据，自动加载下一页
                if (page < 5 && newItems.length === limit) {
                    setTimeout(() => {
                        fetchNews(page + 1, true);
                    }, 800);
                }
            }
        } catch (error) {
            console.error('获取快讯失败:', error);
        }
    };

    const fetchDailyArticles = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/api/public/dailies?type=article&limit=10`);
            const data = await response.json();
            if (data.success && data.data) {
                setDailyArticles(data.data.items || []);
            }
        } catch (error) {
            console.error('获取每日文章失败:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchDailyNews = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/api/public/dailies?type=news&limit=10`);
            const data = await response.json();
            if (data.success && data.data) {
                setDailyNews(data.data.items || []);
            }
        } catch (error) {
            console.error('获取每日快讯失败:', error);
        } finally {
            setLoading(false);
        }
    };

    const formatTime = (dateStr) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000 / 60 / 60);

        if (diff < 1) return `${Math.floor((now - date) / 1000 / 60)}分钟前`;
        if (diff < 24) return `${diff}小时前`;
        return `${Math.floor(diff / 24)}天前`;
    };

    // 过滤逻辑 (使用去抖动后的查询词)
    const filteredArticles = articles.filter(item =>
        !debouncedSearchQuery || item.title.toLowerCase().includes(debouncedSearchQuery.toLowerCase())
    );

    const filteredNews = newsList.filter(item =>
        !debouncedSearchQuery || item.title.toLowerCase().includes(debouncedSearchQuery.toLowerCase())
    );

    // Debug: 检查filteredNews是否更新
    console.log('📊 filteredNews更新:', {
        newsList长度: newsList.length,
        filteredNews长度: filteredNews.length,
        搜索关键词: debouncedSearchQuery,
        第一条ID: filteredNews[0]?.id
    });

    return (
        <div className="bg-gray-100 min-h-screen dark:bg-gray-950 transition-colors duration-300">
            {/* Header */}
            <header className="bg-white border-b border-gray-100 sticky top-0 z-40 bg-opacity-90 backdrop-blur-sm dark:bg-gray-900 dark:border-gray-800 transition-colors duration-300">
                <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white">
                            <Lightning weight="fill" size={18} />
                        </div>
                        <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                            AI News
                        </span>
                    </div>

                    {/* Search Bar - Hidden on Mobile */}
                    <div className="hidden md:flex flex-1 max-w-xl mx-8 relative">
                        <input
                            type="text"
                            placeholder="在这里搜索已加载内容..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full h-10 bg-gray-50 border-none rounded-full px-10 text-sm focus:ring-1 focus:ring-blue-500 transition-all dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-500"
                        />
                        <MagnifyingGlass className="absolute left-3.5 top-2.5 text-gray-400" size={18} />
                    </div>

                    <div className="flex items-center gap-2 md:gap-4">
                        {/* External Links Menu - Click to Toggle */}
                        <div className="relative menu-dropdown">
                            <button
                                onClick={() => setMenuOpen(!menuOpen)}
                                className="px-2 md:px-4 py-2 text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors dark:text-gray-300 dark:hover:text-blue-400 flex items-center gap-1"
                            >
                                <span className="hidden md:inline">链接</span>
                                <CaretDown size={14} className={`transition-transform ${menuOpen ? 'rotate-180' : ''}`} />
                            </button>
                            <div className={`absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-100 transition-all duration-200 dark:bg-gray-800 dark:border-gray-700 ${menuOpen ? 'opacity-100 visible' : 'opacity-0 invisible'
                                }`}>
                                <div className="py-2">
                                    <a
                                        href="https://blacknico.com"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-blue-600 transition-colors dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-blue-400"
                                    >
                                        <span className="flex items-center gap-2">
                                            <FaHome className="text-blue-500" />
                                            主页
                                        </span>
                                    </a>
                                    <a
                                        href="https://t.me/CheshireBTC"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-blue-600 transition-colors dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-blue-400"
                                    >
                                        <span className="flex items-center gap-2">
                                            <FaTelegramPlane className="text-blue-400" />
                                            Telegram 群
                                        </span>
                                    </a>
                                    <a
                                        href="https://x.com/0xCheshire"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-blue-600 transition-colors dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-blue-400"
                                    >
                                        <span className="flex items-center gap-2">
                                            <FaTwitter className="text-sky-500" />
                                            X (Twitter)
                                        </span>
                                    </a>
                                    <a
                                        href="https://blog.blacknico.com/"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-blue-600 transition-colors dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-blue-400"
                                    >
                                        <span className="flex items-center gap-2">
                                            <FaBlog className="text-purple-500" />
                                            博客
                                        </span>
                                    </a>
                                    <a
                                        href="https://github.com/CheshireMew"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-blue-600 transition-colors dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-blue-400"
                                    >
                                        <span className="flex items-center gap-2">
                                            <FaGithub className="text-gray-800 dark:text-gray-200" />
                                            Github
                                        </span>
                                    </a>
                                    <a
                                        href="https://binance.com/join?ref=SRXT5KUM"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-blue-600 transition-colors dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-blue-400"
                                    >
                                        <span className="flex items-center gap-2">
                                            <SiBinance className="text-yellow-500" />
                                            注册币安
                                        </span>
                                    </a>
                                    <a
                                        href="https://okx.com/join/A999998"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-blue-600 transition-colors dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-blue-400"
                                    >
                                        <span className="flex items-center gap-2">
                                            <OKXLogo className="text-gray-800 dark:text-gray-200" />
                                            注册 OKX
                                        </span>
                                    </a>
                                    <a
                                        href="https://0xcheshire.gitbook.io/web3/"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-blue-600 transition-colors dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-blue-400"
                                    >
                                        <span className="flex items-center gap-2">
                                            <FaBook className="text-green-600" />
                                            币圈教程
                                        </span>
                                    </a>
                                </div>
                            </div>
                        </div>

                        <button
                            onClick={() => setDarkMode(!darkMode)}
                            className="p-2 text-gray-400 hover:text-gray-600 transition-colors dark:text-gray-400 dark:hover:text-gray-200"
                            title={darkMode ? "切换到亮色模式" : "切换到暗色模式"}
                        >
                            {darkMode ? <Sun size={20} /> : <Moon size={20} />}
                        </button>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 py-6 w-full flex flex-col md:flex-row gap-6 items-stretch">
                {/* Left: Articles */}
                <div className="w-full md:w-2/3 bg-white rounded-xl shadow-sm border border-gray-100 min-h-[80vh] flex flex-col dark:bg-gray-900 dark:border-gray-800 transition-colors duration-300">
                    {/* Tabs */}
                    <div className="flex items-center px-6 py-4 border-b border-gray-100 sticky top-16 z-30 bg-white rounded-t-xl dark:bg-gray-900 dark:border-gray-800 transition-colors duration-300">
                        <div className="flex gap-1 overflow-x-auto">
                            {['article', 'news', 'daily-article', 'daily-news'].map(tab => {
                                // On mobile, show all tabs. On desktop, hide 'news' tab
                                const isNewsTab = tab === 'news';
                                const hideOnDesktop = isNewsTab ? 'md:hidden' : '';

                                return (
                                    <button
                                        key={tab}
                                        onClick={() => setActiveTab(tab)}
                                        className={`px-3 py-1 text-sm rounded-md font-medium transition-colors whitespace-nowrap ${hideOnDesktop
                                            } ${activeTab === tab
                                                ? 'bg-slate-800 text-white dark:bg-blue-600'
                                                : 'text-gray-500 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-gray-800'
                                            }`}
                                    >
                                        {tab === 'article' ? '文章' : tab === 'news' ? '快讯' : tab === 'daily-article' ? '每日文章' : '每日快讯'}
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Content */}
                    <div className="divide-y divide-gray-50 dark:divide-gray-800">
                        {loading && !loadingMore ? (
                            <div className="p-6 text-center text-gray-400">加载中...</div>
                        ) : activeTab === 'article' ? (
                            <>
                                {filteredArticles.map((article, index) => (
                                    <ArticleItem key={article.id} article={article} index={index + 1} />
                                ))}
                                {/* 底部加载状态 */}
                                <div className="p-4 text-center text-xs text-gray-400">
                                    {loadingMore && <span>正在加载更多...</span>}
                                    {!hasMoreArticles && articles.length > 0 && <span>已加载全部内容</span>}
                                    {searchQuery && filteredArticles.length === 0 && <span>无匹配结果</span>}
                                </div>
                            </>
                        ) : activeTab === 'daily-article' ? (
                            dailyArticles.map((daily, index) => (
                                <DailyReportItem
                                    key={daily.id}
                                    daily={daily}
                                    index={index + 1}
                                    onClick={() => setSelectedReport(daily)}
                                />
                            ))
                        ) : activeTab === 'daily-news' ? (
                            dailyNews.map((daily, index) => (
                                <DailyReportItem
                                    key={daily.id}
                                    daily={daily}
                                    index={index + 1}
                                    onClick={() => setSelectedReport(daily)}
                                />
                            ))
                        ) : activeTab === 'news' ? (
                            <>
                                <div className="p-4 relative">
                                    <div className="absolute left-6 top-4 bottom-4 w-px bg-gray-200 dark:bg-gray-800"></div>
                                    {filteredNews.map((news, index) => (
                                        <NewsItem key={news.id} news={news} />
                                    ))}
                                </div>
                                <div className="p-4 text-center text-xs text-gray-400">
                                    {loadingMore && <span>正在加载更多...</span>}
                                    {!hasMoreNews && newsList.length > 0 && <span>已加载全部内容</span>}
                                    {searchQuery && filteredNews.length === 0 && <span>无匹配结果</span>}
                                </div>
                            </>
                        ) : null}
                    </div>

                    {!loading && (
                        activeTab === 'article' ? articles :
                            activeTab === 'daily-article' ? dailyArticles :
                                activeTab === 'daily-news' ? dailyNews :
                                    activeTab === 'news' ? newsList : []
                    ).length === 0 && (
                            <div className="p-6 text-center text-gray-400">暂无数据</div>
                        )}
                </div>

                {/* Right: 7x24h News (Hidden on Mobile) */}
                <aside className="hidden md:flex w-full md:w-1/3 bg-white rounded-xl shadow-sm border border-gray-100 flex-col dark:bg-gray-900 dark:border-gray-800 transition-colors duration-300">
                    <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 sticky top-16 z-30 bg-white rounded-t-xl dark:bg-gray-900 dark:border-gray-800 transition-colors duration-300">
                        <div className="flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
                            <h2 className="font-bold text-gray-800 text-sm dark:text-gray-200">7x24h 快讯</h2>
                        </div>
                    </div>

                    <div className="p-4 relative">
                        <div className="absolute left-6 top-4 bottom-4 w-px bg-gray-200 dark:bg-gray-800"></div>

                        {filteredNews.map((news, index) => (
                            <NewsItem key={news.id} news={news} />
                        ))}

                        {/* 底部加载状态 */}
                        <div className="mt-4 text-center text-xs text-gray-400 relative z-10 bg-white dark:bg-gray-900">
                            {loadingMore && <span>加载中...</span>}
                            {!hasMoreNews && newsList.length > 0 && <span>已加载全部快讯</span>}
                            {searchQuery && filteredNews.length === 0 && <span>无匹配结果</span>}
                        </div>
                    </div>
                </aside>
            </main>

            {/* Daily Report Modal */}
            {selectedReport && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" onClick={() => setSelectedReport(null)}>
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col overflow-hidden dark:bg-gray-900 dark:border dark:border-gray-800 animate-in fade-in zoom-in duration-200" onClick={e => e.stopPropagation()}>
                        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between dark:border-gray-800">
                            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                                {selectedReport.date} {selectedReport.type === 'article' ? '深度文章合集' : '精选快讯合集'}
                            </h3>
                            <button onClick={() => setSelectedReport(null)} className="text-gray-400 hover:text-gray-600 transition-colors dark:hover:text-gray-200">
                                <span className="text-2xl leading-none">&times;</span>
                            </button>
                        </div>
                        <div className="p-6 overflow-y-auto">
                            <DailyReportContent content={selectedReport.content} />
                        </div>
                        <div className="px-6 py-3 border-t border-gray-100 bg-gray-50 text-right text-xs text-gray-500 dark:bg-gray-800/50 dark:border-gray-800 dark:text-gray-400">
                            发布于 {new Date(selectedReport.created_at).toLocaleString()}
                        </div>
                    </div>
                </div>
            )}

            {/* Floating Buttons */}
            <div className="fixed bottom-8 right-8 flex flex-col items-end gap-3 z-50">
                <button
                    onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                    className="w-12 h-12 bg-white text-gray-600 rounded-full shadow-lg border border-gray-100 flex items-center justify-center hover:bg-gray-50 hover:text-blue-600 transition-all active:scale-95 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700 dark:hover:bg-gray-700"
                    title="回到顶部"
                >
                    <ArrowUp size={20} />
                </button>
            </div>
        </div>
    );
}

// 文章列表项
function ArticleItem({ article, index }) {
    return (
        <div className="flex gap-4 px-6 py-5 hover:bg-gray-50 transition group dark:hover:bg-gray-800/50">
            {/* Index - Hidden on Mobile */}
            <div className="hidden md:block text-gray-300 font-medium text-lg min-w-[20px] dark:text-gray-600">{index}</div>
            <div className="flex-1 min-w-0">
                <h3 className="text-[15px] mb-1 leading-snug">
                    <a href={article.source_url} target="_blank" rel="noopener noreferrer" className="font-bold text-black group-hover:text-blue-600 transition-colors dark:text-gray-200 dark:group-hover:text-blue-400">
                        {article.title}
                    </a>
                </h3>
                <div className="flex flex-wrap items-center gap-2 text-xs text-gray-400 mt-2 dark:text-gray-500">
                    {article.ai_tag && (
                        <span className="px-1.5 py-0.5 rounded uppercase text-[10px] bg-blue-50 text-blue-700 font-medium whitespace-nowrap dark:bg-blue-900/30 dark:text-blue-300">
                            {article.ai_tag}
                        </span>
                    )}
                    <span className="text-gray-500 dark:text-gray-500 truncate">{article.source_site}</span>
                    <span className="whitespace-nowrap">{new Date(article.published_at).toLocaleDateString('zh-CN')}</span>
                </div>
            </div>
        </div>
    );
}

// 日报列表项
function DailyReportItem({ daily, index, onClick }) {
    return (
        <div
            className="flex gap-4 px-6 py-5 hover:bg-gray-50 transition group cursor-pointer dark:hover:bg-gray-800/50"
            onClick={onClick}
        >
            <div className="text-gray-300 font-medium text-lg min-w-[20px] dark:text-gray-600">{index}</div>
            <div className="flex-1">
                <h3 className="text-base font-medium text-slate-800 mb-1 dark:text-gray-200 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                    {daily.date} {daily.type === 'article' ? '深度文章合集' : '精选快讯合集'}
                </h3>
                <div className="flex items-center gap-3 text-xs text-gray-400 mt-2 dark:text-gray-500">
                    <span className="bg-blue-100 text-blue-600 px-1.5 py-0.5 rounded dark:bg-blue-900/30 dark:text-blue-300">
                        {daily.type === 'article' ? '日报' : '快讯'}
                    </span>
                    <span>{daily.date}</span>
                    <span>{daily.news_count} 条内容</span>
                </div>
            </div>
        </div>
    );
}

// 解析并显示日报内容
function DailyReportContent({ content }) {
    // 1. 移除首行标题 (📅 <b>...</b>)
    // 2. 提取链接和标题
    // 原始内容格式: 📰 <a href="...">Title</a>

    // 处理内容：移除头部标题和尾部机器人签名
    const cleanContent = content
        .replace(/^📅.*?(\n\n|<br>)/, '')
        .replace(/(\n\n|<br>)?🤖\s*由.*?自动生成.*/s, '');

    // 提取所有链接 items
    // Regex matches: 📰 <a href="url">Title</a> or just <a href="url">Title</a>
    const regex = /(?:📰\s*)?<a\s+href="([^"]+)">([^<]+)<\/a>/g;
    const items = [];
    let match;

    while ((match = regex.exec(cleanContent)) !== null) {
        items.push({
            url: match[1],
            title: match[2]
        });
    }

    // 如果无法正则匹配（可能是旧格式），则回退到原始 HTML
    if (items.length === 0) {
        return <div className="prose prose-blue max-w-none dark:prose-invert" dangerouslySetInnerHTML={{ __html: content }} />;
    }

    return (
        <div className="space-y-4">
            {items.map((item, index) => (
                <div key={index} className="flex gap-3 items-start group">
                    <span className="text-gray-400 font-medium min-w-[24px] text-right mt-0.5">{index + 1}.</span>
                    <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-gray-800 dark:text-gray-200 hover:text-blue-600 dark:hover:text-blue-400 font-medium leading-normal transition-colors flex-1 block border-b border-transparent hover:border-gray-100 pb-2"
                    >
                        {item.title}
                    </a>
                </div>
            ))}
        </div>
    );
}

// 快讯列表项
function NewsItem({ news }) {
    const formatTime = (dateStr) => {
        const date = new Date(dateStr);
        return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
    };

    return (
        <div className="relative pl-6 mb-4">
            <div className="absolute left-[7px] top-1.5 w-1.5 h-1.5 bg-gray-300 rounded-full border border-white dark:bg-gray-600 dark:border-gray-800"></div>
            <div className="flex items-center gap-2 mb-1">
                <span className="text-xs text-gray-400 dark:text-gray-500">{formatTime(news.published_at)}</span>
                {news.ai_tag && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded uppercase bg-blue-50 text-blue-700 font-medium dark:bg-blue-900/30 dark:text-blue-300">
                        {news.ai_tag}
                    </span>
                )}
            </div>
            <p className="text-sm leading-snug line-clamp-2">
                <a href={news.source_url} target="_blank" rel="noopener noreferrer" className="text-gray-700 hover:text-blue-600 transition-colors dark:text-gray-300 dark:hover:text-blue-400">
                    {news.title}
                </a>
            </p>
        </div>
    );
}
