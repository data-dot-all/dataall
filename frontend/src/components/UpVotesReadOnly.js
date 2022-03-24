import { Box, IconButton, Tooltip, Typography } from '@material-ui/core';
import { ThumbUp } from '@material-ui/icons';
import PropTypes from 'prop-types';
import React from 'react';

const UpVotesReadOnly = (props) => {
  const { upvotes } = props;
  return (
    <Tooltip title="UpVotes">
      <Box sx={{
        alignItems: 'center',
        display: 'flex'
      }}
      >
        <IconButton
          color="primary"
          disabled
        >
          <ThumbUp fontSize="small" />
        </IconButton>

        <Typography
          color="textSecondary"
          variant="subtitle2"
        >
          {upvotes || 0}
        </Typography>
      </Box>
    </Tooltip>
  );
};

UpVotesReadOnly.propTypes = { upvotes: PropTypes.number };

export default UpVotesReadOnly;
