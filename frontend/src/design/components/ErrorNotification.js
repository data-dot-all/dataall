import { CancelRounded } from '@mui/icons-material';
import { IconButton } from '@mui/material';
import { useSnackbar } from 'notistack';
import React, { useEffect } from 'react';
import { HIDE_ERROR, useDispatch, useSelector } from 'globalErrors';

export const ErrorNotification = () => {
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
  }, [error, dispatch, enqueueSnackbar, closeSnackbar]);

  return <></>;
};
