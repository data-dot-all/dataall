// Colors

const neutral = {
  100: '#F3F4F6',
  200: '#E5E7EB',
  300: '#D1D5DB',
  400: '#9CA3AF',
  500: '#6B7280',
  600: '#4B5563',
  700: '#374151',
  800: '#1F2937',
  900: '#111827'
};

const background = {
  default: '#1b2635',
  paper: '#233044',
  hover: '#1b2635'
};

const divider = 'rgba(145, 158, 171, 0.24)';

const primary = {
  main: '#ec7211',
  light: '#f57d26',
  dark: '#cd620e',
  contrastText: '#fff'
};

const secondary = {
  main: '#10B981',
  light: '#3FC79A',
  dark: '#0B815A',
  contrastText: '#fff'
};

const success = {
  main: '#14B8A6',
  light: '#43C6B7',
  dark: '#0E8074',
  contrastText: '#fff'
};

const info = {
  main: '#2196F3',
  light: '#64B6F7',
  dark: '#0B79D0',
  contrastText: '#fff'
};

const warning = {
  main: '#FFB020',
  light: '#FFBF4C',
  dark: '#B27B16',
  contrastText: '#fff'
};

const error = {
  main: '#D14343',
  light: '#DA6868',
  dark: '#922E2E',
  contrastText: '#fff'
};

const text = {
  primary: '#EDF2F7',
  secondary: '#A0AEC0',
  disabled: 'rgba(255, 255, 255, 0.48)'
};

export const darkThemeOptions = {
  components: {
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid rgba(145, 158, 171, 0.24)'
        }
      }
    }
  },
  palette: {
    action: {
      active: neutral[400],
      hover: 'rgba(255, 255, 255, 0.04)',
      selected: 'rgba(255, 255, 255, 0.08)',
      disabledBackground: 'rgba(255, 255, 255, 0.12)',
      disabled: 'rgba(255, 255, 255, 0.26)'
    },
    background,
    divider,
    error,
    info,
    mode: 'dark',
    neutral,
    primary,
    secondary,
    success,
    text,
    warning
  },
  shadows: [
    'none',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 3px 4px -2px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 2px 2px -2px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 3px 4px -2px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 3px 4px -2px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 4px 6px -2px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 4px 6px -2px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 4px 8px -2px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 5px 8px -2px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 6px 12px -4px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 7px 12px -4px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 6px 16px -4px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 7px 16px -4px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 8px 18px -8px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 9px 18px -8px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 10px 20px -8px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 11px 20px -8px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 12px 22px -8px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 13px 22px -8px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 14px 24px -8px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 16px 28px -8px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 18px 30px -8px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 20px 32px -8px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 22px 34px -8px rgba(0,0,0,0.50)',
    '0 0 1px 0 rgba(0,0,0,0.70), 0 24px 36px -8px rgba(0,0,0,0.50)'
  ]
};
