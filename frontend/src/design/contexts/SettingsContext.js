import PropTypes from 'prop-types';
import { createContext, useEffect, useState } from 'react';
import { THEMES } from '../constants';

const initialSettings = {
  compact: true,
  responsiveFontSizes: true,
  roundedCorners: true,
  theme: THEMES.DARK,
  isAdvancedMode: true,
  tabIcons: false
};

const SETTINGS_KEY = 'settings';

export const restoreSettings = () => {
  try {
    const storedSettings = window.localStorage.getItem(SETTINGS_KEY);
    if (storedSettings != null) {
      return JSON.parse(storedSettings);
    }

    const theme = window.matchMedia('(prefers-color-scheme: dark)').matches
      ? THEMES.DARK
      : THEMES.LIGHT;

    return { ...initialSettings, theme: theme };
  } catch (err) {
    console.error(err);
    return null;
  }
};

export const storeSettings = (settings) => {
  window.localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
};

export const SettingsContext = createContext({
  settings: initialSettings,
  saveSettings: () => {}
});

export const SettingsProvider = (props) => {
  const { children } = props;
  const [settings, setSettings] = useState(initialSettings);

  useEffect(() => {
    const restoredSettings = restoreSettings();

    if (restoredSettings) {
      setSettings(restoredSettings);
    }
  }, []);

  const saveSettings = (updatedSettings) => {
    setSettings(updatedSettings);
    storeSettings(updatedSettings);
  };

  return (
    <SettingsContext.Provider
      value={{
        settings,
        saveSettings
      }}
    >
      {children}
    </SettingsContext.Provider>
  );
};

SettingsProvider.propTypes = {
  children: PropTypes.node.isRequired
};

export const SettingsConsumer = SettingsContext.Consumer;
