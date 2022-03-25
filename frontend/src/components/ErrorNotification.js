import React, { useEffect } from 'react';
import { useSnackbar } from 'notistack';
import { IconButton } from '@mui/material';
import { CancelRounded } from '@mui/icons-material';
import { useDispatch, useSelector } from '../store';
import { HIDE_ERROR } from '../store/errorReducer';

const ErrorNotification = () => {
  const dispatch = useDispatch();
  const error = useSelector((state) => state.error.error);
  const { enqueueSnackbar, closeSnackbar } = useSnackbar();
  useEffect(() => {
    if (error) {
      enqueueSnackbar(error, {
        key: new Date().getTime() + Math.random(),
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'error',
        persist: true,
        action: (key) => (
          <IconButton
            onClick={() => {
              dispatch({ type: HIDE_ERROR });
              closeSnackbar(key);
            }}
          >
            <CancelRounded sx={{ color: '#fff' }} />
          </IconButton>
        )
      });
    } else {
      closeSnackbar();
    }
  }, [error]);

  return <></>;
};

export default ErrorNotification;
