import { useCallback, useState } from 'react';
import { message } from 'antd';


export function useFeaturedSelection() {
    const [manuallyFeatured, setManuallyFeatured] = useState([]);

    const handleAddToFeatured = useCallback((record) => {
        setManuallyFeatured((previous) => {
            if (previous.some((item) => item.id === record.id)) {
                message.warning('此内容已在输出列表中');
                return previous;
            }
            message.success('已加入输出列表');
            return [record, ...previous];
        });
    }, []);

    return {
        manuallyFeatured,
        setManuallyFeatured,
        handleAddToFeatured,
    };
}
