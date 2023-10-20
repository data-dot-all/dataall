import { ThemeProvider } from '@mui/material';
import { useRoutes } from 'react-router-dom';
import { useAuth } from './authentication';
import {
  GlobalStyles,
  SplashScreen,
  createMaterialTheme,
  useScrollReset,
  useSettings
} from './design';
import routes from './routes';

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
      {auth.isInitialized ? content : <SplashScreen />}
    </ThemeProvider>
  );
};
