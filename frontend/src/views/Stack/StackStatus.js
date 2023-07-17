import React, { useEffect } from 'react';
import { useSnackbar } from 'notistack';
import {
  Box,
  CircularProgress,
  Grid,
  IconButton,
  Typography
} from '@mui/material';
import { CancelRounded } from '@mui/icons-material';
import PropTypes from 'prop-types';
import { SET_ERROR } from '../../store/errorReducer';
import useClient from '../../hooks/useClient';
import getStack from '../../api/Stack/getStack';
import { useDispatch } from '../../store';

const StackStatus = ({ stack, setStack, environmentUri }) => {
  const { enqueueSnackbar, closeSnackbar } = useSnackbar();
  const client = useClient();
  const dispatch = useDispatch();

  useEffect(() => {
    closeSnackbar();
    if (stack) {
      switch (stack.status) {
        case 'CREATE_IN_PROGRESS':
        case 'UPDATE_IN_PROGRESS':
        case 'REVIEW_IN_PROGRESS':
        case 'PENDING':
          enqueueSnackbar(
            <Box>
              <Grid container spacing={2}>
                <Grid item sx={1}>
                  <CircularProgress sx={{ color: '#fff' }} size={15} />
                </Grid>
                <Grid item sx={11}>
                  <Typography
                    color="textPrimary"
                    sx={{ color: '#fff' }}
                    variant="subtitle2"
                  >
                    AWS CloudFormation stack deployment is in progress !
                  </Typography>
                </Grid>
              </Grid>
            </Box>,
            {
              key: new Date().getTime() + Math.random(),
              anchorOrigin: {
                horizontal: 'right',
                vertical: 'top'
              },
              variant: 'info',
              persist: true,
              action: (key) => (
                <IconButton
                  onClick={() => {
                    closeSnackbar(key);
                  }}
                >
                  <CancelRounded sx={{ color: '#fff' }} />
                </IconButton>
              )
            }
          );
          break;
        case 'CREATE_FAILED':
        case 'DELETE_COMPLETE':
        case 'DELETE_FAILED':
        case 'CREATE_ROLLBACK_COMPLETE':
          enqueueSnackbar(
            <Typography
              color="textPrimary"
              sx={{ color: '#fff' }}
              variant="subtitle2"
            >
              An error occurred during the deployment of the AWS CloudFormation
              stack. Stack status is {stack.status}.
            </Typography>,
            {
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
                    closeSnackbar(key);
                  }}
                >
                  <CancelRounded sx={{ color: '#fff' }} />
                </IconButton>
              )
            }
          );
          break;
        default:
          closeSnackbar();
          break;
      }
    }
    const fetchItem = async () => {
      const response = await client.query(
        getStack(environmentUri, stack.stackUri)
      );
      if (!response.errors && response.data.getStack !== null) {
        setStack(response.data.getStack);
      } else {
        const error = response.errors
          ? response.errors[0].message
          : 'AWS CloudFormation stack not found';
        dispatch({ type: SET_ERROR, error });
      }
    };
    const interval = setInterval(() => {
      if (client && stack) {
        fetchItem().catch((e) =>
          dispatch({ type: SET_ERROR, error: e.message })
        );
      }
    }, 10000);
    return () => clearInterval(interval);
  }, [
    client,
    stack,
    dispatch,
    enqueueSnackbar,
    closeSnackbar,
    environmentUri,
    setStack
  ]);

  return <></>;
};
StackStatus.propTypes = {
  stack: PropTypes.object.isRequired,
  setStack: PropTypes.func.isRequired,
  environmentUri: PropTypes.string.isRequired
};
export default StackStatus;
