import React, { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import { PublicLayout } from './layouts/PublicLayout';
import { useAuthSession } from './auth/useAuthSession';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const NewsFeed = lazy(() => import('./pages/NewsFeed'));

// 路由守卫：保护后台路由
const ProtectedRoute = ({ children }) => {
  const { authenticated } = useAuthSession();
  if (!authenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

const App = () => {
  return (
    <Router>
      <Suspense fallback={null}>
        <Routes>
          {/* 公开路由 - 前台展示 */}
          <Route path="/" element={<PublicLayout />}>
            <Route index element={<NewsFeed />} />
          </Route>

          {/* 登录页面 */}
          <Route path="/login" element={<Login />} />

          {/* 后台管理路由 - 需要认证 */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />

          {/* 默认重定向 */}
          <Route path="/dashboard" element={<Navigate to="/admin" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </Router>
  );
};

export default App;
