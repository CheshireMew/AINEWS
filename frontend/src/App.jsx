import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import NewsFeed from './pages/NewsFeed';
import { PublicLayout } from './layouts/PublicLayout';

// 路由守卫：保护后台路由
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

const App = () => {
  return (
    <Router>
      <Routes>
        {/* 公开路由 - 前台展示 */}
        <Route path="/news" element={<PublicLayout />}>
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

        {/* 默认重定向到前台 */}
        <Route path="/" element={<Navigate to="/news" replace />} />
        <Route path="/dashboard" element={<Navigate to="/admin" replace />} />
        <Route path="*" element={<Navigate to="/news" replace />} />
      </Routes>
    </Router>
  );
};

export default App;
