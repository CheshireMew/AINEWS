import React from 'react';
import { NEWSFEED_TABS } from '../../contracts/content';

export default function NewsFeedTabs({ activeTab, onChange }) {
    return (
        <div className="flex items-center px-6 py-4 border-b border-gray-100 sticky top-16 z-30 bg-white rounded-t-xl dark:bg-gray-900 dark:border-gray-800 transition-colors duration-300">
            <div className="flex gap-1 overflow-x-auto">
                {NEWSFEED_TABS.map(tab => (
                    <button
                        key={tab.key}
                        onClick={() => onChange(tab.key)}
                        className={`px-3 py-1 text-sm rounded-md font-medium transition-colors whitespace-nowrap ${tab.mobileOnly ? 'md:hidden' : ''} ${activeTab === tab.key ? 'bg-slate-800 text-white dark:bg-blue-600' : 'text-gray-500 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-gray-800'}`}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>
        </div>
    );
}
