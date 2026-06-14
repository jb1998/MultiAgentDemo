import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#C8102E', light: '#E63946', dark: '#9B0C24' },
    secondary: { main: '#1A1A1A', light: '#404040', dark: '#000000' },
    background: {
      default: '#FFFFFF',
      paper: '#FFFFFF',
    },
    success: { main: '#15803D' },
    error: { main: '#C8102E' },
    warning: { main: '#B45309' },
    info: { main: '#525252' },
    text: { primary: '#1A1A1A', secondary: '#525252' },
    divider: '#E5E5E5',
  },
  typography: {
    fontFamily: '"Inter", system-ui, sans-serif',
    h1: { fontWeight: 700, letterSpacing: '-0.02em', color: '#1A1A1A' },
    h2: { fontWeight: 700, letterSpacing: '-0.02em', color: '#1A1A1A' },
    h3: { fontWeight: 600, color: '#1A1A1A' },
    button: { textTransform: 'none', fontWeight: 600 },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          background: '#FAFAFA',
          minHeight: '100vh',
          color: '#1A1A1A',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: '#FFFFFF',
          border: '1px solid #E5E5E5',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.06)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#FFFFFF',
          color: '#1A1A1A',
          boxShadow: '0 1px 0 #E5E5E5',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          padding: '10px 24px',
        },
        contained: {
          backgroundColor: '#C8102E',
          color: '#FFFFFF',
          boxShadow: '0 2px 8px rgba(200, 16, 46, 0.25)',
          '&:hover': {
            backgroundColor: '#9B0C24',
            boxShadow: '0 4px 12px rgba(200, 16, 46, 0.35)',
          },
        },
        containedError: {
          backgroundColor: '#1A1A1A',
          '&:hover': { backgroundColor: '#404040' },
        },
        outlined: {
          borderColor: '#D4D4D4',
          color: '#1A1A1A',
          '&:hover': {
            borderColor: '#C8102E',
            backgroundColor: 'rgba(200, 16, 46, 0.04)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
        colorPrimary: {
          backgroundColor: 'rgba(200, 16, 46, 0.1)',
          color: '#C8102E',
        },
        outlined: {
          borderColor: '#D4D4D4',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 10,
            backgroundColor: '#FAFAFA',
            '& fieldset': { borderColor: '#D4D4D4' },
            '&:hover fieldset': { borderColor: '#A3A3A3' },
            '&.Mui-focused fieldset': { borderColor: '#C8102E' },
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderColor: '#E5E5E5',
        },
      },
    },
  },
});

export const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -12 },
  transition: { duration: 0.4, ease: [0.22, 1, 0.36, 1] },
};

export const stagger = {
  animate: { transition: { staggerChildren: 0.08 } },
};
