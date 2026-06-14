import { Box, Container, Grid, Paper, Typography } from '@mui/material';
import { motion } from 'framer-motion';
import TaskInput from '../components/task/TaskInput';
import { useAuthStore } from '../store/authStore';

export default function HomePage() {
  const role = useAuthStore((s) => s.role);
  const isAdmin = role === 'admin';

  const featureCards = [
    { title: 'Smart Routing', desc: 'AI agent picks the best tool for your task' },
    { title: 'Full Trace', desc: 'See every step of agent execution' },
    { title: 'Persistent History', desc: 'All tasks saved and searchable' },
    { title: 'Security Controls', desc: 'PII masking, injection detection, auth checks, and tool input validation protect execution' },
    { title: 'Observability', desc: 'Analytics page shows tool success rates, trace step counts, failures, and runtime metrics' },
    { title: 'Expanded Tools', desc: 'Text, math, weather, date/time, JSON processing, currency, and unit conversion' },
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <Box sx={{ textAlign: 'center', mb: 5 }}>
          <Typography variant="h3" className="gradient-text" fontWeight={700} gutterBottom>
            multiAgent Demo
          </Typography>
          <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto' }}>
            Intelligent agents that route your tasks to the right tools — text processing, math, weather, and more.
          </Typography>
        </Box>
      </motion.div>

      {isAdmin && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {featureCards.map((f, i) => (
            <Grid item xs={12} md={4} key={f.title}>
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}>
                <Paper sx={{ p: 3, height: '100%', textAlign: 'center' }}>
                  <Typography variant="h6" gutterBottom>{f.title}</Typography>
                  <Typography variant="body2" color="text.secondary">{f.desc}</Typography>
                </Paper>
              </motion.div>
            </Grid>
          ))}
        </Grid>
      )}

      <TaskInput />
    </Container>
  );
}
