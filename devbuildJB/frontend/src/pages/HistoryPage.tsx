import { Container } from '@mui/material';
import TaskHistory from '../components/history/TaskHistory';

export default function HistoryPage() {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <TaskHistory />
    </Container>
  );
}
