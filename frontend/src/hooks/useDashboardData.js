import { useDashboardExport } from './dashboard/useDashboardExport';
import { useDashboardOverviewData } from './dashboard/useDashboardOverviewData';
import { useDashboardScraperRuntimeData } from './dashboard/useDashboardScraperRuntimeData';
import { useFeaturedSelection } from './dashboard/useFeaturedSelection';


export function useDashboardData(contentKind) {
    const overview = useDashboardOverviewData(contentKind);
    const runtime = useDashboardScraperRuntimeData();
    const featured = useFeaturedSelection();
    const exportState = useDashboardExport(contentKind);

    return {
        stats: overview.stats,
        spiders: runtime.spiders,
        spiderStatus: runtime.spiderStatus,
        rssSources: runtime.rssSources,
        overview: overview.overview,
        manuallyFeatured: featured.manuallyFeatured,
        setManuallyFeatured: featured.setManuallyFeatured,
        exportState,
        actions: {
            fetchStats: () => overview.refreshOverview({ includeStats: true }),
            fetchOverview: overview.refreshOverview,
            handleAddToFeatured: featured.handleAddToFeatured,
            ...runtime.actions,
        },
    };
}
