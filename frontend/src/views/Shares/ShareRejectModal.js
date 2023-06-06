import PropTypes from 'prop-types';
import {
  Box,
  Button,
  CardContent,
  Dialog,
  FormControlLabel,
  FormGroup,
  Switch,
  TextField,
  Typography
} from '@mui/material';
import React, { useState } from 'react';
import { FaTrash } from 'react-icons/fa';

const ShareRejectModal = (props) => {
  const { share, onApply, onClose, open, rejectFunction, ...other } = props;

  const [rejectPurpose, setRejectPurpose] = useState(null);

  const handleChange = (event) => {
    setRejectPurpose(event.target.value);
  };
  return (
    <Dialog maxWidth="sm" fullWidth onClose={onClose} open={open} {...other}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h4"
        >
          Reject Share
        </Typography>
        <Box sx={{ mt: 2 }}>
          <Typography align="center" variant="subtitle2" color="textSecondary">
            (Optional) Provide a reason for rejecting this share in the text
            input field below:
          </Typography>
          <CardContent>
            <TextField
              fullWidth
              label="reject purpose"
              name="reject"
              onChange={handleChange}
              value={rejectPurpose}
              variant="outlined"
            />
          </CardContent>
          <CardContent>
            <Button
              fullWidth
              startIcon={<FaTrash size={15} />}
              color="error"
              type="submit"
              variant="contained"
              onClick={() => rejectFunction(rejectPurpose)}
            >
              Reject Share
            </Button>
          </CardContent>
        </Box>
      </Box>
    </Dialog>
  );
};

ShareRejectModal.propTypes = {
  share: PropTypes.object.isRequired,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  rejectFunction: PropTypes.func.isRequired,
  open: PropTypes.bool.isRequired,
};

export default ShareRejectModal;
