import { useState } from 'react';

export function useSelectionSet(items) {
    const [selectedIds, setSelectedIds] = useState([]);
    const visibleSelectedIds = selectedIds.filter((id) => items.some((item) => item.id === id));

    const clearSelection = () => {
        setSelectedIds([]);
    };

    const toggleSelectAll = () => {
        if (visibleSelectedIds.length === items.length) {
            setSelectedIds([]);
            return;
        }
        setSelectedIds(items.map((item) => item.id));
    };

    const invertSelection = () => {
        const allIds = items.map((item) => item.id);
        setSelectedIds(allIds.filter((id) => !selectedIds.includes(id)));
    };

    return {
        selectedIds: visibleSelectedIds,
        setSelectedIds,
        clearSelection,
        toggleSelectAll,
        invertSelection,
    };
}
