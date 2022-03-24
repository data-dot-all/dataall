import { createMuiTheme, responsiveFontSizes } from '@material-ui/core/styles';
import { baseThemeOptions } from './BaseThemeOptions';
import { darkThemeOptions } from './DarkThemeOptions';
import { lightThemeOptions } from './LightThemeOptions';
import { THEMES } from '../constants';

export const createTheme = (config) => {
  let theme = createMuiTheme(baseThemeOptions,
    config.theme === THEMES.DARK ? darkThemeOptions : lightThemeOptions,
    {
      direction: config.direction
    },
    { ...(config.roundedCorners ? {
      shape: {
        borderRadius: 16
      }
    } : {
      shape: {
        borderRadius: 8
      }
    })
    });

  if (config.responsiveFontSizes) {
    theme = responsiveFontSizes(theme);
  }
  /*
  default: '#1b2635',
        paper: '#233044'
        contrastText: '#ffffff',
        main: '#ec7211'
   */

  return theme;
};
