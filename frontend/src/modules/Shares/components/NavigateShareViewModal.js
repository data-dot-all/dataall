import { Box, Dialog, Divider, Typography, Button } from '@mui/material';
import PropTypes from 'prop-types';
import { Link as RouterLink } from 'react-router-dom';

export const NavigateShareViewModal = (props) => {
  const { dataset, onApply, onClose, open, ...other } = props;

  return (
    <Dialog maxWidth="md" fullWidth onClose={onClose} open={open} {...other}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h4"
        >
          Dataset: {dataset.label} - Share Object Verification Task(s) Started
        </Typography>
        <Typography
          align="center"
          color="textSecondary"
          variant="subtitle2"
          sx={{ p: 1 }}
        >
          Navigate to the Share View Page and select the desired share object to
          view the progress of each of verification task
        </Typography>
        <Divider />
        <Button
          sx={{ p: 1 }}
          color="primary"
          type="button"
          fullWidth
          component={RouterLink}
          to={`/console/shares`}
          variant="contained"
        >
          Navigate to Shares View
        </Button>
        <Button
          sx={{ p: 1 }}
          onClick={onClose}
          fullWidth
          color="primary"
          variant="outlined"
        >
          Close
        </Button>
      </Box>
    </Dialog>
  );
};

NavigateShareViewModal.propTypes = {
  shares: PropTypes.array.isRequired,
  dataset: PropTypes.object.isRequired,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired
};
