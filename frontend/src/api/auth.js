import client from './client';
import { setAuthToken } from '../auth/session';

export const login = async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    const res = await client.post('/login', formData);
    const auth = res.data;
    if (auth.access_token) {
        setAuthToken(auth.access_token);
    }
    return auth;
};

export const updateCredentials = (data) => client.post('/system/credentials', data);
