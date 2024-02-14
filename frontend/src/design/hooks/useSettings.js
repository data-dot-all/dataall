import { useContext } from 'react';
import { SettingsContext } from 'design/contexts';

export const useSettings = () => useContext(SettingsContext);
