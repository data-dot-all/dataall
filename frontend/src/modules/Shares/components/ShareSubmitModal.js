import PropTypes from 'prop-types';
import * as Yup from 'yup';
import { Formik } from 'formik';
import {
  Box,
  CardContent,
  Dialog,
  TextField,
  FormHelperText,
  Typography,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody
} from '@mui/material';
import { LoadingButton } from '@mui/lab';
import SendIcon from '@mui/icons-material/Send';
import React from 'react';
import { updateShareRequestReason } from '../services';
import { SET_ERROR } from '../../../globalErrors';
import { ShareStatus } from '../../../design';

export const ShareSubmitModal = (props) => {
  const {
    share,
    onApply,
    onClose,
    open,
    submitFunction,
    client,
    dispatch,
    enqueueSnackbar,
    fetchItem,
    sharedItems,
    ...other
  } = props;

  const updatePurpose = async (comment) => {
    const response = await client.mutate(
      updateShareRequestReason({
        shareUri: share.shareUri,
        requestPurpose: comment
      })
    );
    if (!response.errors) {
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
  };

  return (
    <Dialog maxWidth="sm" fullWidth onClose={onClose} open={open} {...other}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h4"
        >
          Submit Share
        </Typography>
        <Box sx={{ mt: 2 }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Type</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sharedItems.nodes.length > 0 ? (
                sharedItems.nodes.map((sharedItem) => (
                  <TableRow>
                    <TableCell>{sharedItem.itemType}</TableCell>
                    <TableCell>{sharedItem.itemName}</TableCell>
                    <TableCell>
                      <ShareStatus status={sharedItem.status} />
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell>No items added.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Box>
        <Box sx={{ mt: 2 }}>
          <Typography align="center" variant="subtitle2" color="textSecondary">
            (Optional) Provide a reason for requesting this share in the text
            input field below:
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
              if (values.comment !== share.requestPurpose) {
                await updatePurpose(values.comment);
              }
              await submitFunction(values.comment);
              onClose();
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
                    Submit Share
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

ShareSubmitModal.propTypes = {
  share: PropTypes.object.isRequired,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  submitFunction: PropTypes.func.isRequired,
  open: PropTypes.bool.isRequired,
  sharedItems: PropTypes.any
};
