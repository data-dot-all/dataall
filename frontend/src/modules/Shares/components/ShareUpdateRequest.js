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
import { updateShareRequestReason } from '../services';
import { PencilAltIcon } from 'design';

export const UpdateRequestReason = (props) => {
  const { share, client, dispatch, enqueueSnackbar, fetchItem, ...other } =
    props;
  const [isUpdateRequestModalOpen, setIsUpdateRequestModalOpen] =
    useState(false);
  const [updating, setUpdating] = useState(false);

  const handleUpdateRequestModalOpen = () => {
    setIsUpdateRequestModalOpen(true);
  };
  const handleUpdateRequestModalClose = () => {
    setIsUpdateRequestModalOpen(false);
  };
  const update = async (comment) => {
    setUpdating(true);
    const response = await client.mutate(
      updateShareRequestReason({
        shareUri: share.shareUri,
        requestPurpose: comment
      })
    );
    if (!response.errors) {
      handleUpdateRequestModalClose();
      enqueueSnackbar('Share request reason updated', {
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
        onClick={handleUpdateRequestModalOpen}
        loading={updating}
        color="primary"
      />
      <Dialog
        maxWidth="sm"
        fullWidth
        onClose={handleUpdateRequestModalClose}
        open={isUpdateRequestModalOpen}
        {...other}
      >
        <Box sx={{ p: 3 }}>
          <Typography
            align="center"
            color="textPrimary"
            gutterBottom
            variant="h4"
          >
            Update Share Request
          </Typography>
          <Box sx={{ mt: 2 }}>
            <Typography
              align="center"
              variant="subtitle2"
              color="textSecondary"
            >
              Update a reason for your share request:
            </Typography>
          </Box>
          <Box sx={{ p: 3 }}>
            <Formik
              initialValues={{
                comment: share.requestPurpose ? share.requestPurpose : ''
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
                        label="Request purpose"
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
                      Update Share Request
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

UpdateRequestReason.propTypes = {
  share: PropTypes.any,
  client: PropTypes.any,
  dispatch: PropTypes.any,
  enqueueSnackbar: PropTypes.any,
  fetchItem: PropTypes.func
};
