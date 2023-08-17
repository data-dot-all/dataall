import { createTheme, responsiveFontSizes } from '@mui/material/styles';
import { THEMES } from '../constants';
import { baseThemeOptions } from './BaseThemeOptions';
import { darkThemeOptions } from './DarkThemeOptions';
import { lightThemeOptions } from './LightThemeOptions';

export const createMaterialTheme = (config) => {
  let theme = createTheme(
    baseThemeOptions,
    config.theme === THEMES.DARK ? darkThemeOptions : lightThemeOptions,
    {
      direction: config.direction
    },
    {
      ...(config.roundedCorners
        ? {
            shape: {
              borderRadius: 16
            }
          }
        : {
            shape: {
              borderRadius: 8
            }
          })
    }
  );

  if (config.responsiveFontSizes) {
    theme = responsiveFontSizes(theme);
  }
  return theme;
};
