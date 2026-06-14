import {
  Alert,
  Box,
  Button,
  Container,
  Paper,
  Tab,
  Tabs,
  TextField,
  Typography,
} from '@mui/material';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import { motion } from 'framer-motion';
import { useState } from 'react';
import { login, register } from '../services/taskService';
import { useAuthStore } from '../store/authStore';

interface Props {
  onSuccess: () => void;
}

export default function LoginPage({ onSuccess }: Props) {
  const [tab, setTab] = useState(0);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const setAuth = useAuthStore((s) => s.setAuth);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const data = await login(username, password);
      setAuth(data.access_token, data.username, data.role);
      onSuccess();
    } catch {
      setError('Invalid username or password');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const data = await register(username, email, password);
      setAuth(data.access_token, data.username, data.role);
      onSuccess();
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      setError(msg || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#FAFAFA',
      }}
    >
      <Container maxWidth="sm">
        <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}>
          <Paper sx={{ p: 5, textAlign: 'center' }}>
            <AutoAwesomeIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography variant="h4" className="gradient-text" fontWeight={700} gutterBottom>
              multiAgent Demo
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Multi-agent task execution with RBAC &amp; security controls
            </Typography>

            <Tabs value={tab} onChange={(_, v) => { setTab(v); setError(''); }} sx={{ mb: 3 }}>
              <Tab label="Sign In" />
              <Tab label="Register" />
            </Tabs>

            {tab === 0 ? (
              <Box component="form" onSubmit={handleLogin}>
                <TextField
                  fullWidth
                  label="Username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  sx={{ mb: 2 }}
                  required
                />
                <TextField
                  fullWidth
                  label="Password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  sx={{ mb: 3 }}
                  required
                />
                {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
                <Button fullWidth variant="contained" size="large" type="submit" disabled={loading}>
                  {loading ? 'Signing in...' : 'Sign In'}
                </Button>
              </Box>
            ) : (
              <Box component="form" onSubmit={handleRegister}>
                <TextField
                  fullWidth
                  label="Username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  sx={{ mb: 2 }}
                  required
                />
                <TextField
                  fullWidth
                  label="Email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  sx={{ mb: 2 }}
                  required
                />
                <TextField
                  fullWidth
                  label="Password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  helperText="Minimum 8 characters"
                  sx={{ mb: 3 }}
                  required
                />
                {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
                <Button fullWidth variant="contained" size="large" type="submit" disabled={loading}>
                  {loading ? 'Creating account...' : 'Create Account'}
                </Button>
              </Box>
            )}

            <Box sx={{ mt: 3, textAlign: 'left' }}>
              <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                Demo accounts:
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block">
                Admin: admin / admin1234 — full access (analytics, all users, delete tasks)
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block">
                User: user / user1234 — submit tasks &amp; view own history
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block">
                Rate-limited: test1 / test1 — 5 task quota (then blocked)
              </Typography>
            </Box>
          </Paper>
        </motion.div>
      </Container>
    </Box>
  );
}
