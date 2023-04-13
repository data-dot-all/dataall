import PropTypes from 'prop-types';
import {
  Box,
  Button,
  CardContent,
  Dialog,
  TextField,
  Typography
} from '@mui/material';
import { useState } from 'react';
import { ArchiveOutlined } from '@mui/icons-material';

export const ArchiveObjectWithFrictionModal = (props) => {
  const {
    objectName,
    archiveMessage,
    onApply,
    onClose,
    open,
    archiveFunction,
    ...other
  } = props;
  const [confirmValue, setConfirmValue] = useState(null);

  const handleChange = (event) => {
    setConfirmValue(event.target.value);
  };
  return (
    <Dialog maxWidth="sm" fullWidth onClose={onClose} open={open} {...other}>
      <Box sx={{ p: 3 }}>
        <Box sx={{ mb: 5 }}>
          <Typography
            align="center"
            color="textPrimary"
            gutterBottom
            variant="h4"
          >
            Archive {objectName} ?
          </Typography>
        </Box>

        {archiveMessage && <Box sx={{ mt: 1 }}>{archiveMessage}</Box>}

        <CardContent>
          <TextField
            fullWidth
            label="To confirm archival, type permanently archive in the text input field"
            name="confirm"
            onChange={handleChange}
            value={confirmValue}
            variant="outlined"
          />
        </CardContent>
        <CardContent>
          <Button
            fullWidth
            disabled={confirmValue !== 'permanently archive'}
            startIcon={<ArchiveOutlined fontSize="small" />}
            color="error"
            type="submit"
            variant="contained"
            onClick={() => {
              archiveFunction();
            }}
          >
            Archive
          </Button>
        </CardContent>
      </Box>
    </Dialog>
  );
};

ArchiveObjectWithFrictionModal.propTypes = {
  objectName: PropTypes.string.isRequired,
  archiveMessage: PropTypes.string,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  archiveFunction: PropTypes.func.isRequired,
  open: PropTypes.bool.isRequired
};
