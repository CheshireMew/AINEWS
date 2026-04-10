import React from 'react';

export function ArticleItem({ item, index }) {
    return (
        <div className="flex gap-4 px-6 py-5 hover:bg-gray-50 transition group dark:hover:bg-gray-800/50">
            <div className="hidden md:block text-gray-300 font-medium text-lg min-w-[20px] dark:text-gray-600">{index}</div>
            <div className="flex-1 min-w-0">
                <h3 className="text-[15px] mb-1 leading-snug">
                    <a href={item.source_url} target="_blank" rel="noopener noreferrer" className="font-bold text-black group-hover:text-blue-600 transition-colors dark:text-gray-200 dark:group-hover:text-blue-400">
                        {item.title}
                    </a>
                </h3>
                <div className="flex flex-wrap items-center gap-2 text-xs text-gray-400 mt-2 dark:text-gray-500">
                    {item.ai_tag && <span className="px-1.5 py-0.5 rounded uppercase text-[10px] bg-blue-50 text-blue-700 font-medium whitespace-nowrap dark:bg-blue-900/30 dark:text-blue-300">{item.ai_tag}</span>}
                    <span className="text-gray-500 dark:text-gray-500 truncate">{item.source_site}</span>
                    <span className="whitespace-nowrap">{new Date(item.published_at).toLocaleDateString('zh-CN')}</span>
                </div>
            </div>
        </div>
    );
}

export default function ArticleList({ items, loadingMore, hasMore, searchQuery }) {
    return (
        <>
            {items.map((item, index) => (
                <ArticleItem key={item.id} item={item} index={index + 1} />
            ))}
            <div className="p-4 text-center text-xs text-gray-400">
                {loadingMore && <span>正在加载更多...</span>}
                {!hasMore && items.length > 0 && <span>已加载全部内容</span>}
                {searchQuery && items.length === 0 && <span>无匹配结果</span>}
            </div>
        </>
    );
}
