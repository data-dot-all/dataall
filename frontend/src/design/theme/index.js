import { createTheme, responsiveFontSizes } from '@mui/material/styles';
import { THEMES } from 'design/constants';
import { baseThemeOptions } from 'design/theme/BaseThemeOptions';
import { darkThemeOptions } from 'design/theme/DarkThemeOptions';
import { lightThemeOptions } from 'design/theme/LightThemeOptions';

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
