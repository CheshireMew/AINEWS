import { useSyncExternalStore } from 'react';

import { clearAuthToken, getAuthToken, setAuthToken, subscribeAuthSession } from './session';

export function useAuthSession() {
    const token = useSyncExternalStore(
        subscribeAuthSession,
        getAuthToken,
        () => null,
    );

    return {
        token,
        authenticated: Boolean(token),
        login: setAuthToken,
        logout: clearAuthToken,
    };
}
