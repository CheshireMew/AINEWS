import { useEffect, useMemo, useState } from 'react';
import { FEED_TAB } from '../../contracts/content';

export function useNewsFeedUiState() {
    const [activeTab, setActiveTab] = useState(FEED_TAB.LONGFORM);
    const [searchQuery, setSearchQuery] = useState('');
    const [debouncedSearchQuery, setDebouncedSearchQuery] = useState('');
    const [selectedReport, setSelectedReport] = useState(null);
    const [menuOpen, setMenuOpen] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedSearchQuery(searchQuery);
        }, 800);
        return () => clearTimeout(timer);
    }, [searchQuery]);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (menuOpen && !event.target.closest('.menu-dropdown')) {
                setMenuOpen(false);
            }
        };
        document.addEventListener('click', handleClickOutside);
        return () => document.removeEventListener('click', handleClickOutside);
    }, [menuOpen]);

    return useMemo(() => ({
        activeTab,
        setActiveTab,
        searchQuery,
        setSearchQuery,
        debouncedSearchQuery,
        selectedReport,
        setSelectedReport,
        menuOpen,
        setMenuOpen,
    }), [activeTab, searchQuery, debouncedSearchQuery, selectedReport, menuOpen]);
}
