import React from 'react';
import { Modal, Box, Typography, Button } from '@mui/material';
import SampleDataTableComponent from './SampleDataTableComponent';

const SampleDataPopup = ({
  open,
  sampleData,
  handleClose,
  handleRegenerate
}) => {
  return (
    <Modal open={open} onClose={handleClose}>
      <Box
        sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          bgcolor: 'background.paper',
          boxShadow: 24,
          p: 4
        }}
      >
        <Typography variant="h6" component="h2">
          Sample Data
        </Typography>
        <SampleDataTableComponent data={sampleData} />
        <Button variant="contained" color="primary" onClick={handleRegenerate}>
          Accept and Regenerate
        </Button>
      </Box>
    </Modal>
  );
};

export default SampleDataPopup;
