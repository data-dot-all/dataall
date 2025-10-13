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
import { PencilAltIcon } from 'design';
import { updateShareExtensionReason } from '../services/updateShareExtensionReason';

export const UpdateExtensionReason = (props) => {
  const { share, client, dispatch, enqueueSnackbar, fetchItem, ...other } =
    props;
  const [isUpdateExtensionModalOpen, setIsUpdateExtensionModalOpen] =
    useState(false);
  const [updating, setUpdating] = useState(false);

  const handleUpdateExtensionModalOpen = () => {
    setIsUpdateExtensionModalOpen(true);
  };
  const handleUpdateExtensionModalClose = () => {
    setIsUpdateExtensionModalOpen(false);
  };
  const update = async (comment) => {
    setUpdating(true);
    const response = await client.mutate(
      updateShareExtensionReason({
        shareUri: share.shareUri,
        extensionPurpose: comment
      })
    );
    if (!response.errors) {
      handleUpdateExtensionModalClose();
      enqueueSnackbar('Share extension reason updated', {
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
        onClick={handleUpdateExtensionModalOpen}
        loading={updating}
        color="primary"
      />
      <Dialog
        maxWidth="sm"
        fullWidth
        onClose={handleUpdateExtensionModalClose}
        open={isUpdateExtensionModalOpen}
        {...other}
      >
        <Box sx={{ p: 3 }}>
          <Typography
            align="center"
            color="textPrimary"
            gutterBottom
            variant="h4"
          >
            Update Share Extension Reason
          </Typography>
          <Box sx={{ mt: 2 }}>
            <Typography
              align="center"
              variant="subtitle2"
              color="textSecondary"
            >
              Update a reason to extend the share request:
            </Typography>
          </Box>
          <Box sx={{ p: 3 }}>
            <Formik
              initialValues={{
                comment: share.extensionReason ? share.extensionReason : ''
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
                        label="Extension purpose"
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
                      Update Share Extension Reason
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

UpdateExtensionReason.propTypes = {
  share: PropTypes.any,
  client: PropTypes.any,
  dispatch: PropTypes.any,
  enqueueSnackbar: PropTypes.any,
  fetchItem: PropTypes.func
};
