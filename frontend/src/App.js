import { ThemeProvider } from '@mui/material';
import { useRoutes } from 'react-router-dom';
import {
  GlobalStyles,
  createMaterialTheme,
  useScrollReset,
  useSettings,
  LoadingScreen, SplashScreen
} from './design';
import routes from './routes';
import { useAuth } from './authentication';
import {isMaintenanceMode} from "./services/graphql/MaintenanceWindow";

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
      {/*{auth.isInitialized ?  isMaintenanceMode() ? content : <SplashScreen /> : <LoadingScreen />}*/}
      {auth.isInitialized ?  content :  <LoadingScreen />}
    </ThemeProvider>
  );
};
