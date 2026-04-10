import React from 'react';
import { CaretDown, Lightning, MagnifyingGlass, Moon, Sun } from '@phosphor-icons/react';
import { FaHome, FaTelegramPlane, FaTwitter, FaBlog, FaGithub, FaBook } from 'react-icons/fa';
import { SiBinance } from 'react-icons/si';

const OKXLogo = ({ className }) => (
    <svg viewBox="0 0 24 24" className={className} fill="currentColor" width="1em" height="1em">
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="13" y="3" width="7" height="7" rx="1.5" />
        <rect x="8" y="8" width="7" height="7" rx="1.5" />
        <rect x="3" y="13" width="7" height="7" rx="1.5" />
        <rect x="13" y="13" width="7" height="7" rx="1.5" />
    </svg>
);

export default function NewsFeedHeader({ searchQuery, onSearchChange, menuOpen, onToggleMenu, darkMode, onToggleDarkMode }) {
    return (
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

                <div className="hidden md:flex flex-1 max-w-xl mx-8 relative">
                    <input
                        type="text"
                        placeholder="搜索公开内容..."
                        value={searchQuery}
                        onChange={(e) => onSearchChange(e.target.value)}
                        className="w-full h-10 bg-gray-50 border-none rounded-full px-10 text-sm focus:ring-1 focus:ring-blue-500 transition-all dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-500"
                    />
                    <MagnifyingGlass className="absolute left-3.5 top-2.5 text-gray-400" size={18} />
                </div>

                <div className="flex items-center gap-2 md:gap-4">
                    <div className="relative menu-dropdown">
                        <button
                            onClick={onToggleMenu}
                            className="px-2 md:px-4 py-2 text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors dark:text-gray-300 dark:hover:text-blue-400 flex items-center gap-1"
                        >
                            <span className="hidden md:inline">链接</span>
                            <CaretDown size={14} className={`transition-transform ${menuOpen ? 'rotate-180' : ''}`} />
                        </button>
                        <div className={`absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-100 transition-all duration-200 dark:bg-gray-800 dark:border-gray-700 ${menuOpen ? 'opacity-100 visible' : 'opacity-0 invisible'}`}>
                            <div className="py-2">
                                <a href="https://blacknico.com" target="_blank" rel="noopener noreferrer" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-blue-600 transition-colors dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-blue-400"><span className="flex items-center gap-2"><FaHome className="text-blue-500" />主页</span></a>
                                <a href="https://t.me/CheshireBTC" target="_blank" rel="noopener noreferrer" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-blue-600 transition-colors dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-blue-400"><span className="flex items-center gap-2"><FaTelegramPlane className="text-blue-400" />Telegram 群</span></a>
                                <a href="https://x.com/0xCheshire" target="_blank" rel="noopener noreferrer" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-blue-600 transition-colors dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-blue-400"><span className="flex items-center gap-2"><FaTwitter className="text-sky-500" />X (Twitter)</span></a>
                                <a href="https://blog.blacknico.com/" target="_blank" rel="noopener noreferrer" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-blue-600 transition-colors dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-blue-400"><span className="flex items-center gap-2"><FaBlog className="text-purple-500" />博客</span></a>
                                <a href="https://github.com/CheshireMew" target="_blank" rel="noopener noreferrer" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-blue-600 transition-colors dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-blue-400"><span className="flex items-center gap-2"><FaGithub className="text-gray-800 dark:text-gray-200" />Github</span></a>
                                <a href="https://binance.com/join?ref=SRXT5KUM" target="_blank" rel="noopener noreferrer" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-blue-600 transition-colors dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-blue-400"><span className="flex items-center gap-2"><SiBinance className="text-yellow-500" />注册币安</span></a>
                                <a href="https://okx.com/join/A999998" target="_blank" rel="noopener noreferrer" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-blue-600 transition-colors dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-blue-400"><span className="flex items-center gap-2"><OKXLogo className="text-gray-800 dark:text-gray-200" />注册 OKX</span></a>
                                <a href="https://0xcheshire.gitbook.io/web3/" target="_blank" rel="noopener noreferrer" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-blue-600 transition-colors dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-blue-400"><span className="flex items-center gap-2"><FaBook className="text-green-600" />币圈教程</span></a>
                            </div>
                        </div>
                    </div>

                    <button
                        onClick={onToggleDarkMode}
                        className="p-2 text-gray-400 hover:text-gray-600 transition-colors dark:text-gray-400 dark:hover:text-gray-200"
                        title={darkMode ? '切换到亮色模式' : '切换到暗色模式'}
                    >
                        {darkMode ? <Sun size={20} /> : <Moon size={20} />}
                    </button>
                </div>
            </div>
        </header>
    );
}
