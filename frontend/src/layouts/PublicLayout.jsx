import { Outlet } from 'react-router-dom';

export function PublicLayout() {
    return (
        <div className="public-layout min-h-screen bg-gray-50">
            <Outlet />
        </div>
    );
}
