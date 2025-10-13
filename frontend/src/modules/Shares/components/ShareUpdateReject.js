import PropTypes from 'prop-types';
import * as Yup from 'yup';
import { Formik } from 'formik';
import {
  Box,
  CardContent,
  Dialog,
  TextField,
  FormHelperText,
  Typography
} from '@mui/material';
import { LoadingButton } from '@mui/lab';
import { SET_ERROR } from 'globalErrors';
import SendIcon from '@mui/icons-material/Send';
import React, { useState } from 'react';
import { updateShareRejectReason } from '../services';
import { PencilAltIcon } from 'design';

export const UpdateRejectReason = (props) => {
  const { share, client, dispatch, enqueueSnackbar, fetchItem, ...other } =
    props;
  const [isUpdateRejectModalOpen, setIsUpdateRejectModalOpen] = useState(false);
  const [updating, setUpdating] = useState(false);

  const handleUpdateRejectModalOpen = () => {
    setIsUpdateRejectModalOpen(true);
  };
  const handleUpdateRejectModalClose = () => {
    setIsUpdateRejectModalOpen(false);
  };
  const update = async (comment) => {
    setUpdating(true);
    const response = await client.mutate(
      updateShareRejectReason({
        shareUri: share.shareUri,
        rejectPurpose: comment
      })
    );
    if (!response.errors) {
      handleUpdateRejectModalClose();
      enqueueSnackbar('Share reject reason updated', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      await fetchItem();
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setUpdating(false);
  };

  return (
    <>
      <PencilAltIcon
        fontSize="small"
        onClick={handleUpdateRejectModalOpen}
        loading={updating}
        color="primary"
      />
      <Dialog
        maxWidth="sm"
        fullWidth
        onClose={handleUpdateRejectModalClose}
        open={isUpdateRejectModalOpen}
        {...other}
      >
        <Box sx={{ p: 3 }}>
          <Typography
            align="center"
            color="textPrimary"
            gutterBottom
            variant="h4"
          >
            Update Share Reject Reason
          </Typography>
          <Box sx={{ mt: 2 }}>
            <Typography
              align="center"
              variant="subtitle2"
              color="textSecondary"
            >
              Update a reason to reject the share request:
            </Typography>
          </Box>
          <Box sx={{ p: 3 }}>
            <Formik
              initialValues={{
                comment: share.rejectPurpose ? share.rejectPurpose : ''
              }}
              validationSchema={Yup.object().shape({
                comment: Yup.string().max(200)
              })}
              onSubmit={async (values) => {
                await update(values.comment);
              }}
            >
              {({
                errors,
                handleBlur,
                handleChange,
                handleSubmit,
                isSubmitting,
                setFieldValue,
                touched,
                values
              }) => (
                <form onSubmit={handleSubmit}>
                  <Box>
                    <CardContent>
                      <TextField
                        FormHelperTextProps={{
                          sx: {
                            textAlign: 'right',
                            mr: 0
                          }
                        }}
                        fullWidth
                        helperText={`${
                          200 - values.comment.length
                        } characters left`}
                        label="Reject purpose"
                        name="comment"
                        multiline
                        onBlur={handleBlur}
                        onChange={handleChange}
                        rows={5}
                        value={values.comment}
                        variant="outlined"
                      />
                      {touched.comment && errors.comment && (
                        <Box sx={{ mt: 2 }}>
                          <FormHelperText error>
                            {errors.comment}
                          </FormHelperText>
                        </Box>
                      )}
                    </CardContent>
                  </Box>
                  <CardContent>
                    <LoadingButton
                      fullWidth
                      startIcon={<SendIcon fontSize="small" />}
                      color="primary"
                      disabled={isSubmitting}
                      type="submit"
                      variant="contained"
                    >
                      Update Share Reject Reason
                    </LoadingButton>
                  </CardContent>
                </form>
              )}
            </Formik>
          </Box>
        </Box>
      </Dialog>
    </>
  );
};

UpdateRejectReason.propTypes = {
  share: PropTypes.any,
  client: PropTypes.any,
  dispatch: PropTypes.any,
  enqueueSnackbar: PropTypes.any,
  fetchItem: PropTypes.func
};
