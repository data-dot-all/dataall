import {
  Box,
  Button,
  Drawer,
  FormControlLabel,
  IconButton,
  Switch,
  TextField,
  Tooltip,
  Typography
} from '@mui/material';
import { useEffect, useState } from 'react';
import { THEMES } from '../constants';
import { useSettings } from '../hooks';
import { AdjustmentsIcon } from '../icons';

const getValues = (settings) => ({
  compact: settings.compact,
  direction: settings.direction,
  responsiveFontSizes: settings.responsiveFontSizes,
  roundedCorners: settings.roundedCorners,
  theme: settings.theme,
  isAdvancedMode: settings.isAdvancedMode,
  tabIcons: settings.tabIcons
});

export const SettingsDrawer = () => {
  const { settings, saveSettings } = useSettings();
  const [open, setOpen] = useState(false);
  const [values, setValues] = useState(getValues(settings));

  useEffect(() => {
    setValues(getValues(settings));
  }, [settings]);

  const handleOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleChange = (field, value) => {
    setValues({
      ...values,
      [field]: value
    });
  };

  const handleSave = () => {
    saveSettings(values);
    setOpen(false);
  };

  return (
    <>
      <Tooltip title="Settings">
        <IconButton color="inherit" onClick={handleOpen}>
          <AdjustmentsIcon fontSize="small" />
        </IconButton>
      </Tooltip>
      <Drawer
        anchor="right"
        onClose={handleClose}
        open={open}
        style={{ zIndex: 1250 }}
        PaperProps={{
          sx: {
            p: 2,
            width: 320
          }
        }}
      >
        <Typography color="textPrimary" variant="h6">
          Settings
        </Typography>
        <Box sx={{ mt: 3 }}>
          <TextField
            fullWidth
            label="Theme"
            name="theme"
            onChange={(event) => handleChange('theme', event.target.value)}
            select
            SelectProps={{ native: true }}
            value={values.theme}
            variant="outlined"
          >
            {Object.keys(THEMES).map((theme) => (
              <option key={theme} value={theme}>
                {theme
                  .split('_')
                  .map((w) => w[0].toUpperCase() + w.substr(1).toLowerCase())
                  .join(' ')}
              </option>
            ))}
          </TextField>
        </Box>
        <Box
          sx={{
            mt: 2,
            px: 1.5
          }}
        >
          <FormControlLabel
            control={
              <Switch
                checked={values.isAdvancedMode}
                color="primary"
                edge="start"
                name="isAdvancedMode"
                onChange={(event) =>
                  handleChange('isAdvancedMode', !!event.target.checked)
                }
              />
            }
            label={
              <div>
                Advanced UX
                <Typography
                  color="textSecondary"
                  component="p"
                  variant="caption"
                >
                  Add advanced users menus and options
                </Typography>
              </div>
            }
          />
        </Box>
        <Box
          sx={{
            mt: 2,
            px: 1.5
          }}
        >
          <FormControlLabel
            control={
              <Switch
                checked={values.tabIcons}
                color="primary"
                edge="start"
                name="tabIcons"
                onChange={(event) =>
                  handleChange('tabIcons', event.target.checked)
                }
              />
            }
            label={
              <div>
                Tab Icons
                <Typography
                  color="textSecondary"
                  component="p"
                  variant="caption"
                >
                  Show tabs icons
                </Typography>
              </div>
            }
          />
        </Box>
        <Box
          sx={{
            mt: 2,
            px: 1.5
          }}
        >
          <FormControlLabel
            control={
              <Switch
                checked={values.roundedCorners}
                color="primary"
                edge="start"
                name="roundedCorners"
                onChange={(event) =>
                  handleChange('roundedCorners', event.target.checked)
                }
              />
            }
            label={
              <div>
                Rounded Corners
                <Typography
                  color="textSecondary"
                  component="p"
                  variant="caption"
                >
                  Increase border radius
                </Typography>
              </div>
            }
          />
        </Box>
        <Box sx={{ mt: 3 }}>
          <Button
            color="primary"
            fullWidth
            onClick={handleSave}
            variant="contained"
          >
            Save Settings
          </Button>
        </Box>
      </Drawer>
    </>
  );
};
