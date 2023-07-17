import { useEffect, useState } from 'react';
import { IconButton, Tooltip } from '@mui/material';
import useSettings from '../../hooks/useSettings';
import { THEMES } from '../../constants';
import MoonIcon from '../../icons/Moon';
import SunIcon from '../../icons/Sun';

const ThemePopover = () => {
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

export default ThemePopover;
