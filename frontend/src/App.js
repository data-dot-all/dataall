import { ThemeProvider } from '@mui/material';
import { SnackbarProvider } from 'notistack';
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

  console.log('hello');

  const theme = createMaterialTheme({
    direction: settings.direction,
    responsiveFontSizes: settings.responsiveFontSizes,
    roundedCorners: settings.roundedCorners,
    theme: settings.theme
  });

  return (
    <ThemeProvider theme={theme}>
      <SnackbarProvider dense maxSnack={3} hideIconVariant>
        <GlobalStyles />
        {auth.isInitialized ? content : <SplashScreen />}
      </SnackbarProvider>
    </ThemeProvider>
  );
};
