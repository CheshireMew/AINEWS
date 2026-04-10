import { useEffect, useMemo } from 'react';

import { CONTENT_KIND, FEED_TAB, PUBLIC_STREAM } from '../contracts/content';
import { useNewsFeedUiState } from './newsfeed/useNewsFeedUiState';
import { usePublicReportFeed } from './newsfeed/usePublicReportFeed';
import { usePublicSearchResults } from './newsfeed/usePublicSearchResults';
import { usePublicStream } from './newsfeed/usePublicStream';
import { useThemePreference } from './newsfeed/useThemePreference';

const REFRESH_INTERVAL_MS = 60000;

function matchesTitle(item, query) {
    return !query || item.title.toLowerCase().includes(query.toLowerCase());
}

export function useNewsFeedData() {
    const ui = useNewsFeedUiState();
    const theme = useThemePreference();
    const longform = usePublicStream(PUBLIC_STREAM.LONGFORM);
    const briefs = usePublicStream(PUBLIC_STREAM.BRIEFS);
    const articleReports = usePublicReportFeed(CONTENT_KIND.ARTICLE);
    const briefReports = usePublicReportFeed(CONTENT_KIND.NEWS);
    const search = usePublicSearchResults(ui.debouncedSearchQuery);
    const {
        state: longformState,
        ensureLoaded: ensureLongformLoaded,
        refresh: refreshLongform,
        loadMore: loadMoreLongform,
    } = longform;
    const {
        state: briefsState,
        ensureLoaded: ensureBriefsLoaded,
        refresh: refreshBriefs,
        loadMore: loadMoreBriefs,
    } = briefs;
    const {
        state: articleReportState,
        ensureLoaded: ensureArticleReportsLoaded,
    } = articleReports;
    const {
        state: briefReportState,
        ensureLoaded: ensureBriefReportsLoaded,
    } = briefReports;
    const {
        state: searchState,
        enabled: searchEnabled,
    } = search;

    useEffect(() => {
        const timer = setTimeout(() => {
            void ensureBriefsLoaded();
            if (ui.activeTab === FEED_TAB.LONGFORM) {
                void ensureLongformLoaded();
            }
            if (ui.activeTab === FEED_TAB.ARTICLE_REPORTS) {
                void ensureArticleReportsLoaded();
            }
            if (ui.activeTab === FEED_TAB.BRIEF_REPORTS) {
                void ensureBriefReportsLoaded();
            }
        }, 0);
        return () => clearTimeout(timer);
    }, [ensureArticleReportsLoaded, ensureBriefReportsLoaded, ensureBriefsLoaded, ensureLongformLoaded, ui.activeTab]);

    useEffect(() => {
        const activeStream = ui.activeTab === FEED_TAB.LONGFORM
            ? { state: longformState, loadMore: loadMoreLongform }
            : ui.activeTab === FEED_TAB.BRIEFS
                ? { state: briefsState, loadMore: loadMoreBriefs }
                : null;
        if (!activeStream) {
            return undefined;
        }

        const handleScroll = () => {
            if (searchEnabled) {
                return;
            }
            const current = activeStream.state;
            if (!current.loaded || !current.hasMore || current.loadingMore) {
                return;
            }
            const nearBottom = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 500;
            if (!nearBottom) {
                return;
            }
            void activeStream.loadMore();
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, [briefsState, loadMoreBriefs, loadMoreLongform, longformState, searchEnabled, ui.activeTab]);

    useEffect(() => {
        const interval = setInterval(() => {
            if (searchEnabled) {
                return;
            }
            void refreshBriefs();
            if (longformState.loaded) {
                void refreshLongform();
            }
        }, REFRESH_INTERVAL_MS);

        return () => clearInterval(interval);
    }, [longformState.loaded, refreshBriefs, refreshLongform, searchEnabled]);

    const searchQuery = ui.debouncedSearchQuery.trim();
    const visibleLongformItems = useMemo(
        () => (searchEnabled ? searchState.articleItems : longformState.items),
        [longformState.items, searchEnabled, searchState.articleItems],
    );
    const visibleBriefItems = useMemo(
        () => (searchEnabled ? searchState.briefItems : briefsState.items),
        [briefsState.items, searchEnabled, searchState.briefItems],
    );
    const filteredArticleReports = useMemo(
        () => articleReportState.items.filter((item) => matchesTitle(item, searchQuery)),
        [articleReportState.items, searchQuery],
    );
    const filteredBriefReports = useMemo(
        () => briefReportState.items.filter((item) => matchesTitle(item, searchQuery)),
        [briefReportState.items, searchQuery],
    );
    const currentItems = useMemo(() => {
        if (ui.activeTab === FEED_TAB.LONGFORM) return visibleLongformItems;
        if (ui.activeTab === FEED_TAB.ARTICLE_REPORTS) return filteredArticleReports;
        if (ui.activeTab === FEED_TAB.BRIEF_REPORTS) return filteredBriefReports;
        if (ui.activeTab === FEED_TAB.BRIEFS) return visibleBriefItems;
        return [];
    }, [filteredArticleReports, filteredBriefReports, ui.activeTab, visibleBriefItems, visibleLongformItems]);

    const loading = (
        (ui.activeTab === FEED_TAB.LONGFORM && (searchEnabled ? searchState.loading : longformState.loading))
        || (ui.activeTab === FEED_TAB.ARTICLE_REPORTS && articleReportState.loading)
        || (ui.activeTab === FEED_TAB.BRIEF_REPORTS && briefReportState.loading)
        || (ui.activeTab === FEED_TAB.BRIEFS && (searchEnabled ? searchState.loading : briefsState.loading))
    );
    const loadingMore = searchEnabled
        ? false
        : (ui.activeTab === FEED_TAB.LONGFORM ? longformState.loadingMore : ui.activeTab === FEED_TAB.BRIEFS ? briefsState.loadingMore : false);

    return {
        state: {
            activeTab: ui.activeTab,
            loading,
            loadingMore,
            searchQuery: ui.searchQuery,
            selectedReport: ui.selectedReport,
            menuOpen: ui.menuOpen,
            darkMode: theme.darkMode,
            hasMoreLongform: longformState.hasMore,
            hasMoreBriefs: briefsState.hasMore,
            articleReports: filteredArticleReports,
            briefReports: filteredBriefReports,
            visibleLongformItems,
            visibleBriefItems,
            currentItems,
        },
        actions: {
            setActiveTab: ui.setActiveTab,
            setSearchQuery: ui.setSearchQuery,
            setSelectedReport: ui.setSelectedReport,
            setMenuOpen: ui.setMenuOpen,
            setDarkMode: theme.setDarkMode,
        },
    };
}
