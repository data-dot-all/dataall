import { IconButton, Tooltip } from '@mui/material';
import { useEffect, useState } from 'react';
import { THEMES } from 'design/constants';
import { useSettings } from 'design/hooks';
import { MoonIcon, SunIcon } from 'design/icons';

export const ThemePopover = () => {
  const { settings, saveSettings } = useSettings();
  const [selectedTheme, setSelectedTheme] = useState(settings.theme);

  useEffect(() => {
    setSelectedTheme(settings.theme);
  }, [settings.theme]);

  const handleSwitch = () =>
    saveSettings({
      ...settings,
      theme: settings.theme === THEMES.LIGHT ? THEMES.DARK : THEMES.LIGHT
    });

  return (
    <>
      <Tooltip title="Switch themes">
        <IconButton onClick={handleSwitch}>
          {selectedTheme === 'LIGHT' ? (
            <MoonIcon sx={{ color: 'white' }} fontSize="small" />
          ) : (
            <SunIcon color="inherit" fontSize="small" />
          )}
        </IconButton>
      </Tooltip>
    </>
  );
};
