import { AppBar, Box, Button, Chip, Container, Toolbar, Typography } from '@mui/material';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import { motion } from 'framer-motion';
import { Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';

const baseNavItems = [
  { path: '/', label: 'Home' },
  { path: '/history', label: 'History' },
];

const adminNavItems = [
  { path: '/analytics', label: 'Analytics' },
  { path: '/admin', label: 'Admin Dashboard' },
  { path: '/costs', label: 'Cost Tracking' },
];

export default function Header() {
  const location = useLocation();
  const { username, role, logout } = useAuthStore();
  const navItems = role === 'admin' ? [...baseNavItems, ...adminNavItems] : baseNavItems;

  return (
    <AppBar
      position="sticky"
      elevation={0}
      sx={{
        bgcolor: '#FFFFFF',
        borderBottom: '1px solid #E5E5E5',
      }}
    >
      <Container maxWidth="lg">
        <Toolbar disableGutters sx={{ gap: 2, py: 1 }}>
          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Box component={Link} to="/" sx={{ display: 'flex', alignItems: 'center', gap: 1, textDecoration: 'none', color: 'inherit' }}>
              <AutoAwesomeIcon sx={{ color: 'primary.main' }} />
              <Typography variant="h6" className="gradient-text" fontWeight={700}>
                multiAgent Demo
              </Typography>
            </Box>
          </motion.div>

          <Box sx={{ flex: 1, display: 'flex', gap: 1, ml: 4 }}>
            {navItems.map((item) => (
              <Button
                key={item.path}
                component={Link}
                to={item.path}
                sx={{
                  color: location.pathname === item.path ? 'primary.main' : 'text.secondary',
                  background: location.pathname === item.path ? 'rgba(200, 16, 46, 0.08)' : 'transparent',
                  fontWeight: location.pathname === item.path ? 600 : 400,
                }}
              >
                {item.label}
              </Button>
            ))}
          </Box>

          <Chip
            label={role === 'admin' ? 'Admin' : 'User'}
            size="small"
            color={role === 'admin' ? 'secondary' : 'default'}
            variant="outlined"
          />
          <Typography variant="body2" color="text.secondary">
            {username}
          </Typography>
          <Button size="small" variant="outlined" onClick={logout}>
            Logout
          </Button>
        </Toolbar>
      </Container>
    </AppBar>
  );
}
