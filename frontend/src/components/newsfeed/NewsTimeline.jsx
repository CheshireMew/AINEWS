import React from 'react';

export function NewsItem({ item }) {
    const formatTime = (dateStr) => {
        const date = new Date(dateStr);
        return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
    };

    return (
        <div className="relative pl-6 mb-4">
            <div className="absolute left-[7px] top-1.5 w-1.5 h-1.5 bg-gray-300 rounded-full border border-white dark:bg-gray-600 dark:border-gray-800"></div>
            <div className="flex items-center gap-2 mb-1">
                <span className="text-xs text-gray-400 dark:text-gray-500">{formatTime(item.published_at)}</span>
                {item.ai_tag && <span className="text-[10px] px-1.5 py-0.5 rounded uppercase bg-blue-50 text-blue-700 font-medium dark:bg-blue-900/30 dark:text-blue-300">{item.ai_tag}</span>}
            </div>
            <p className="text-sm leading-snug line-clamp-2">
                <a href={item.source_url} target="_blank" rel="noopener noreferrer" className="text-gray-700 hover:text-blue-600 transition-colors dark:text-gray-300 dark:hover:text-blue-400">
                    {item.title}
                </a>
            </p>
        </div>
    );
}

export default function NewsTimeline({ items, loadingMore, hasMore, searchQuery, compact = false }) {
    const containerClass = compact ? '' : 'p-4 relative';
    return (
        <>
            <div className={containerClass}>
                <div className="absolute left-6 top-4 bottom-4 w-px bg-gray-200 dark:bg-gray-800"></div>
                {items.map((item) => (
                    <NewsItem key={item.id} item={item} />
                ))}
            </div>
            <div className={`${compact ? 'p-4' : 'mt-4'} text-center text-xs text-gray-400 relative z-10 bg-white dark:bg-gray-900`}>
                {loadingMore && <span>{compact ? '正在加载更多...' : '加载中...'}</span>}
                {!hasMore && items.length > 0 && <span>{compact ? '已加载全部内容' : '已加载全部快讯'}</span>}
                {searchQuery && items.length === 0 && <span>无匹配结果</span>}
            </div>
        </>
    );
}
