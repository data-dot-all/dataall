import { Box, IconButton, Tooltip, Typography } from '@mui/material';
import { ThumbUp } from '@mui/icons-material';
import PropTypes from 'prop-types';
import React from 'react';

export const UpVotesReadOnly = (props) => {
  const { upvotes } = props;
  return (
    <Tooltip title="UpVotes">
      <Box
        sx={{
          alignItems: 'center',
          display: 'flex'
        }}
      >
        <IconButton color="primary" disabled>
          <ThumbUp fontSize="small" />
        </IconButton>

        <Typography color="textSecondary" variant="subtitle2">
          {upvotes || 0}
        </Typography>
      </Box>
    </Tooltip>
  );
};

UpVotesReadOnly.propTypes = { upvotes: PropTypes.number };
