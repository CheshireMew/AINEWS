import React from 'react';
import PropTypes from 'prop-types';
import { useExportDelivery } from '../../hooks/dashboard/useExportDelivery';
import { useExportItems } from '../../hooks/dashboard/useExportItems';
import { useSelectionSet } from '../../hooks/dashboard/useSelectionSet';
import ExportFiltersPanel from './ExportFiltersPanel';
import ExportItemsTable from './ExportItemsTable';
import ExportSelectionToolbar from './ExportSelectionToolbar';

const ExportTab = ({ manuallyFeatured, setManuallyFeatured, contentKind }) => {
    const {
        exportTimeRange,
        exportMinScore,
        visibleItems,
        loading,
        setExportTimeRange,
        setExportMinScore,
        loadItems,
    } = useExportItems(contentKind, manuallyFeatured, setManuallyFeatured);
    const {
        selectedIds,
        setSelectedIds,
        clearSelection,
        toggleSelectAll,
        invertSelection,
    } = useSelectionSet(visibleItems);
    const {
        sendingToTg,
        copyPlainText,
        copyMarkdown,
        copyTelegramHtml,
        sendToTelegram,
        triggerDailyDelivery,
    } = useExportDelivery(contentKind, visibleItems, selectedIds);

    return (
        <div style={{ padding: '0 10px' }}>
            <ExportFiltersPanel
                exportTimeRange={exportTimeRange}
                exportMinScore={exportMinScore}
                loading={loading}
                setExportTimeRange={setExportTimeRange}
                setExportMinScore={setExportMinScore}
                loadItems={loadItems}
                triggerDailyDelivery={triggerDailyDelivery}
            />
            <ExportSelectionToolbar
                visibleCount={visibleItems.length}
                selectedCount={selectedIds.length}
                sendingToTg={sendingToTg}
                clearSelection={clearSelection}
                toggleSelectAll={toggleSelectAll}
                invertSelection={invertSelection}
                copyPlainText={copyPlainText}
                copyMarkdown={copyMarkdown}
                copyTelegramHtml={copyTelegramHtml}
                sendToTelegram={sendToTelegram}
            />
            <ExportItemsTable
                visibleItems={visibleItems}
                loading={loading}
                selectedIds={selectedIds}
                setSelectedIds={setSelectedIds}
            />
        </div>
    );
};

ExportTab.propTypes = {
    manuallyFeatured: PropTypes.arrayOf(PropTypes.object),
    setManuallyFeatured: PropTypes.func,
    contentKind: PropTypes.string,
};

export default ExportTab;
