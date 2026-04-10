import React from 'react';
import { ArrowUp } from '@phosphor-icons/react';

import { useNewsFeedData } from '../hooks/useNewsFeedData';
import NewsFeedHeader from '../components/newsfeed/NewsFeedHeader';
import NewsFeedTabs from '../components/newsfeed/NewsFeedTabs';
import ArticleList from '../components/newsfeed/ArticleList';
import NewsTimeline from '../components/newsfeed/NewsTimeline';
import DailyReportModal, { DailyReportItem } from '../components/newsfeed/DailyReportModal';
import { FEED_TAB } from '../contracts/content';

export default function NewsFeed() {
    const { state, actions } = useNewsFeedData();
    const {
        activeTab,
        loading,
        loadingMore,
        searchQuery,
        selectedReport,
        menuOpen,
        darkMode,
        hasMoreLongform,
        hasMoreBriefs,
        articleReports,
        briefReports,
        visibleLongformItems,
        visibleBriefItems,
        currentItems,
    } = state;
    const {
        setActiveTab,
        setSearchQuery,
        setSelectedReport,
        setMenuOpen,
        setDarkMode,
    } = actions;

    return (
        <div className="bg-gray-100 min-h-screen dark:bg-gray-950 transition-colors duration-300">
            <NewsFeedHeader
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                menuOpen={menuOpen}
                onToggleMenu={() => setMenuOpen(!menuOpen)}
                darkMode={darkMode}
                onToggleDarkMode={() => setDarkMode(!darkMode)}
            />

            <main className="max-w-7xl mx-auto px-4 py-6 w-full flex flex-col md:flex-row gap-6 items-stretch">
                <div className="w-full md:w-2/3 bg-white rounded-xl shadow-sm border border-gray-100 min-h-[80vh] flex flex-col dark:bg-gray-900 dark:border-gray-800 transition-colors duration-300">
                    <NewsFeedTabs activeTab={activeTab} onChange={setActiveTab} />

                    <div className="divide-y divide-gray-50 dark:divide-gray-800">
                        {loading && !loadingMore ? (
                            <div className="p-6 text-center text-gray-400">加载中...</div>
                        ) : activeTab === FEED_TAB.LONGFORM ? (
                            <ArticleList items={visibleLongformItems} loadingMore={loadingMore} hasMore={hasMoreLongform} searchQuery={searchQuery} />
                        ) : activeTab === FEED_TAB.ARTICLE_REPORTS ? (
                            articleReports.map((report, index) => (
                                <DailyReportItem key={report.id} report={report} index={index + 1} onClick={() => setSelectedReport(report)} />
                            ))
                        ) : activeTab === FEED_TAB.BRIEF_REPORTS ? (
                            briefReports.map((report, index) => (
                                <DailyReportItem key={report.id} report={report} index={index + 1} onClick={() => setSelectedReport(report)} />
                            ))
                        ) : activeTab === FEED_TAB.BRIEFS ? (
                            <NewsTimeline items={visibleBriefItems} loadingMore={loadingMore} hasMore={hasMoreBriefs} searchQuery={searchQuery} compact />
                        ) : null}
                    </div>

                    {!loading && currentItems.length === 0 && (
                        <div className="p-6 text-center text-gray-400">暂无数据</div>
                    )}
                </div>

                <aside className="hidden md:flex w-full md:w-1/3 bg-white rounded-xl shadow-sm border border-gray-100 flex-col dark:bg-gray-900 dark:border-gray-800 transition-colors duration-300">
                    <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 sticky top-16 z-30 bg-white rounded-t-xl dark:bg-gray-900 dark:border-gray-800 transition-colors duration-300">
                        <div className="flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
                            <h2 className="font-bold text-gray-800 text-sm dark:text-gray-200">7x24h 快讯</h2>
                        </div>
                    </div>
                    <NewsTimeline items={visibleBriefItems} loadingMore={loadingMore} hasMore={hasMoreBriefs} searchQuery={searchQuery} />
                </aside>
            </main>

            <DailyReportModal report={selectedReport} onClose={() => setSelectedReport(null)} />

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
