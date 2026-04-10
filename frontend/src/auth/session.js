const TOKEN_KEY = 'token';
const listeners = new Set();
let storageListenerBound = false;

function notifyListeners() {
    listeners.forEach((listener) => listener());
}

function bindStorageListener() {
    if (storageListenerBound || typeof window === 'undefined') {
        return;
    }
    window.addEventListener('storage', (event) => {
        if (event.key === TOKEN_KEY) {
            notifyListeners();
        }
    });
    storageListenerBound = true;
}

export function subscribeAuthSession(listener) {
    bindStorageListener();
    listeners.add(listener);
    return () => {
        listeners.delete(listener);
    };
}

export function getAuthToken() {
    return localStorage.getItem(TOKEN_KEY);
}

export function setAuthToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
    notifyListeners();
}

export function clearAuthToken() {
    localStorage.removeItem(TOKEN_KEY);
    notifyListeners();
}

export function hasAuthToken() {
    return Boolean(getAuthToken());
}
