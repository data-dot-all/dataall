import React from 'react';
import { Modal, Box, Button, Typography } from '@mui/material';
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
        <SampleDataTableComponent data={sampleData} />

        <Box
          sx={{
            mt: 3,
            mb: 2,
            p: 2,
            backgroundColor: 'rgba(0, 0, 0, 0.03)',
            borderRadius: 1,
            border: '1px solid rgba(0, 0, 0, 0.1)'
          }}
        >
          <Typography
            variant="body1"
            color="text.secondary"
            fontWeight="medium"
          >
            By clicking the button below, you agree to share this sample data
            with a third-party language model.
          </Typography>
        </Box>

        <Box display="flex" justifyContent="flex-end">
          <Button
            variant="contained"
            color="primary"
            onClick={handleRegenerate}
          >
            Accept and Regenerate
          </Button>{' '}
        </Box>
      </Box>
    </Modal>
  );
};

export default SampleDataPopup;
