import PropTypes from 'prop-types';
import { Box, Dialog, Divider, Typography } from '@mui/material';
import React from 'react';

export const TableSchemaModal = (props) => {
  const { onClose, open, rsTableUri } = props;

  return (
    <Dialog maxWidth="md" fullWidth onClose={onClose} open={open}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h4"
        >
          Redshift table {rsTableUri}
        </Typography>
        <Divider />
      </Box>
    </Dialog>
  );
};
TableSchemaModal.propTypes = {
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired,
  rsTableUri: PropTypes.string.isRequired
};
