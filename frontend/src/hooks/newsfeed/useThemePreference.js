import { useEffect, useState } from 'react';

export function useThemePreference() {
    const [darkMode, setDarkMode] = useState(() => {
        if (typeof window === 'undefined') {
            return false;
        }
        return localStorage.getItem('theme') === 'dark'
            || (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches);
    });

    useEffect(() => {
        if (darkMode) {
            document.documentElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
            return;
        }
        document.documentElement.classList.remove('dark');
        localStorage.setItem('theme', 'light');
    }, [darkMode]);

    return { darkMode, setDarkMode };
}
