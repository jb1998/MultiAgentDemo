import { CssBaseline, ThemeProvider } from '@mui/material';
import { AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import Header from './components/layout/Header';
import AdminPage from './pages/AdminPage';
import AdminDashboardPage from './pages/AdminDashboardPage';
import CostTrackingPage from './pages/CostTrackingPage';
import HistoryPage from './pages/HistoryPage';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import { useAuthStore } from './store/authStore';
import { theme } from './styles/theme';
import './styles/global.css';

function AdminRoute({ children }: { children: React.ReactNode }) {
  const role = useAuthStore((s) => s.role);
  if (role !== 'admin') {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}

function AppRoutes() {
  const token = useAuthStore((s) => s.token);
  const [ready, setReady] = useState(!!token);

  if (!token) {
    return <LoginPage onSuccess={() => setReady(true)} />;
  }

  if (!ready) return null;

  return (
    <>
      <Header />
      <AnimatePresence mode="wait">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route
            path="/analytics"
            element={
              <AdminRoute>
                <AdminPage />
              </AdminRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <AdminDashboardPage />
              </AdminRoute>
            }
          />
          <Route
            path="/costs"
            element={
              <AdminRoute>
                <CostTrackingPage />
              </AdminRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AnimatePresence>
    </>
  );
}

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </ThemeProvider>
  );
}
