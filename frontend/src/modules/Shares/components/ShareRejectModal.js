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
import SendIcon from '@mui/icons-material/Send';
import React from 'react';

export const ShareRejectModal = (props) => {
  const { share, onApply, onClose, open, rejectFunction, ...other } = props;

  return (
    <Dialog maxWidth="sm" fullWidth onClose={onClose} open={open} {...other}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h4"
        >
          Reject Share {share.submittedForExtension ? 'Extension' : ''}
        </Typography>
        <Box sx={{ mt: 2 }}>
          <Typography align="center" variant="subtitle2" color="textSecondary">
            (Optional) Provide a reason for rejecting this share in the text
            input field below:
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
              await rejectFunction(values.comment);
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
                        <FormHelperText error>{errors.comment}</FormHelperText>
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
                    Reject Share{' '}
                    {share.submittedForExtension ? 'Extension' : ''}
                  </LoadingButton>
                </CardContent>
              </form>
            )}
          </Formik>
        </Box>
      </Box>
    </Dialog>
  );
};

ShareRejectModal.propTypes = {
  share: PropTypes.object.isRequired,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  rejectFunction: PropTypes.func.isRequired,
  open: PropTypes.bool.isRequired
};
