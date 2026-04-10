import { message } from 'antd';

export function getRequestErrorMessage(error, fallback = '请求失败') {
    return error?.message || fallback;
}

export async function refreshListPage(
    listState,
    {
        page = listState.pagination.current,
        pageSize = listState.pagination.pageSize,
        source = listState.filterSource,
        keyword = listState.filterKeyword,
    } = {},
) {
    await listState.fetchItems(page, pageSize, source, keyword);
}

export async function runListAction({
    action,
    successMessage,
    errorMessage,
    listState,
    refresh = 'current',
    refreshOptions,
}) {
    try {
        const result = await action();
        message.success(typeof successMessage === 'function' ? successMessage(result) : successMessage);
        if (refresh === 'first-page') {
            await refreshListPage(listState, { page: 1, ...refreshOptions });
            return result;
        }
        await listState.refreshCurrent();
        return result;
    } catch (error) {
        message.error(`${errorMessage}: ${getRequestErrorMessage(error, errorMessage)}`);
        return null;
    }
}
