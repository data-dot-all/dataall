import { ThemeProvider } from '@mui/material';
import { useRoutes } from 'react-router-dom';
import {
  GlobalStyles,
  createMaterialTheme,
  useScrollReset,
  useSettings,
  LoadingScreen
} from './design';
import routes from './routes';
import { useAuth } from './authentication';

export const App = () => {
  const content = useRoutes(routes);
  const { settings } = useSettings();
  const auth = useAuth();
  useScrollReset();

  const theme = createMaterialTheme({
    direction: settings.direction,
    responsiveFontSizes: settings.responsiveFontSizes,
    roundedCorners: settings.roundedCorners,
    theme: settings.theme
  });

  return (
    <ThemeProvider theme={theme}>
      <GlobalStyles />
      {auth.isInitialized ? content : <LoadingScreen />}
    </ThemeProvider>
  );
};
