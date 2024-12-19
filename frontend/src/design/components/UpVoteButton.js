import { Button } from '@mui/material';
import { ThumbUpAlt, ThumbUpOffAlt } from '@mui/icons-material';
import * as PropTypes from 'prop-types';
import React from 'react';

export const UpVoteButton = (props) => {
  const { upVoted, onClick, upVotes, disabled } = props;
  return (
    <Button
      color="primary"
      disabled={disabled}
      startIcon={
        upVoted ? (
          <ThumbUpAlt fontSize="small" />
        ) : (
          <ThumbUpOffAlt fontSize="small" />
        )
      }
      onClick={onClick}
      sx={{ mt: 1, mr: 1 }}
      variant={upVoted ? 'contained' : 'outlined'}
    >
      {upVotes}
    </Button>
  );
};

UpVoteButton.propTypes = {
  upVoted: PropTypes.bool,
  onClick: PropTypes.func,
  upVotes: PropTypes.any,
  disabled: PropTypes.bool
};
