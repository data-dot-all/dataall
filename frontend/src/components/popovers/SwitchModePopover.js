import { IconButton, Tooltip } from '@material-ui/core';
import useSettings from '../../hooks/useSettings';
import Refresh from '../../icons/Refresh';

/**
 * @description Toggle "advanced" / "basic" mode.
 * @returns {JSX.Element}
 */
const SwitchModePopover = () => {
  const { settings, saveSettings } = useSettings();

  /**
   * @description Toggle mode.
   */
  const handleSwitch = () => saveSettings({
    ...settings,
    isAdvancedMode: !settings.isAdvancedMode
  });

  return (
    <Tooltip title="Switch mode">
      <IconButton onClick={handleSwitch}>
        <Refresh
          fontSize="small"
        />
      </IconButton>
    </Tooltip>
  );
};

export default SwitchModePopover;
