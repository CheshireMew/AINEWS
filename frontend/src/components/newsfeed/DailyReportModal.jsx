import React from 'react';

export function DailyReportItem({ report, index, onClick }) {
    const isLongform = report.type === 'article';
    return (
        <div className="flex gap-4 px-6 py-5 hover:bg-gray-50 transition group cursor-pointer dark:hover:bg-gray-800/50" onClick={onClick}>
            <div className="text-gray-300 font-medium text-lg min-w-[20px] dark:text-gray-600">{index}</div>
            <div className="flex-1">
                <h3 className="text-base font-medium text-slate-800 mb-1 dark:text-gray-200 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                    {report.date} {isLongform ? '深度文章合集' : '精选快讯合集'}
                </h3>
                <div className="flex items-center gap-3 text-xs text-gray-400 mt-2 dark:text-gray-500">
                    <span className="bg-blue-100 text-blue-600 px-1.5 py-0.5 rounded dark:bg-blue-900/30 dark:text-blue-300">
                        {isLongform ? '日报' : '快讯'}
                    </span>
                    <span>{report.date}</span>
                    <span>{report.news_count} 条内容</span>
                </div>
            </div>
        </div>
    );
}

export function DailyReportContent({ content }) {
    const cleanContent = content
        .replace(/^📅.*?(\n\n|<br>)/, '')
        .replace(/(\n\n|<br>)?🤖\s*由.*?自动生成.*/s, '');

    const regex = /(?:📰\s*)?<a\s+href="([^"]+)">([^<]+)<\/a>/g;
    const items = [];
    let match;
    while ((match = regex.exec(cleanContent)) !== null) {
        items.push({ url: match[1], title: match[2] });
    }

    if (items.length === 0) {
        return <div className="prose prose-blue max-w-none dark:prose-invert" dangerouslySetInnerHTML={{ __html: content }} />;
    }

    return (
        <div className="space-y-4">
            {items.map((item, index) => (
                <div key={index} className="flex gap-3 items-start group">
                    <span className="text-gray-400 font-medium min-w-[24px] text-right mt-0.5">{index + 1}.</span>
                    <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-gray-800 dark:text-gray-200 hover:text-blue-600 dark:hover:text-blue-400 font-medium leading-normal transition-colors flex-1 block border-b border-transparent hover:border-gray-100 pb-2">
                        {item.title}
                    </a>
                </div>
            ))}
        </div>
    );
}

export default function DailyReportModal({ report, onClose }) {
    if (!report) return null;
    const isLongform = report.type === 'article';

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" onClick={onClose}>
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col overflow-hidden dark:bg-gray-900 dark:border dark:border-gray-800 animate-in fade-in zoom-in duration-200" onClick={e => e.stopPropagation()}>
                <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between dark:border-gray-800">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                        {report.date} {isLongform ? '深度文章合集' : '精选快讯合集'}
                    </h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors dark:hover:text-gray-200">
                        <span className="text-2xl leading-none">&times;</span>
                    </button>
                </div>
                <div className="p-6 overflow-y-auto">
                    <DailyReportContent content={report.content} />
                </div>
                <div className="px-6 py-3 border-t border-gray-100 bg-gray-50 text-right text-xs text-gray-500 dark:bg-gray-800/50 dark:border-gray-800 dark:text-gray-400">
                    发布于 {new Date(report.created_at).toLocaleString()}
                </div>
            </div>
        </div>
    );
}
