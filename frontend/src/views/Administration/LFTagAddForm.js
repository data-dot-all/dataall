import React, { useCallback, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { useSnackbar } from 'notistack';
import {
  Autocomplete,
  Box,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  Dialog,
  Divider,
  FormControlLabel,
  FormGroup,
  FormHelperText,
  MenuItem,
  Paper,
  Switch,
  TextField,
  Typography
} from '@mui/material';
import { Formik } from 'formik';
import * as Yup from 'yup';
import { LoadingButton } from '@mui/lab';
import { GroupAddOutlined } from '@mui/icons-material';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import useClient from '../../hooks/useClient';
import * as Defaults from '../../components/defaults';
import addLFTag from '../../api/LFTags/addLFTag'
import ChipInput from '../../components/TagsInput';


const LFTagAddForm = (props) => {
  const { onClose, open, reloadTags, ...other } = props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(addLFTag
        ({
          LFTagKey: values.LFTagKey,
          LFTagValues: values.LFTagValues,
          description: values.description
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('LF Tag Added', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        if (reloadTags) {
            reloadTags();
          }
        if (onClose) {
          onClose();
        }
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (err) {
      console.error(err);
      setStatus({ success: false });
      setErrors({ submit: err.message });
      setSubmitting(false);
      dispatch({ type: SET_ERROR, error: err.message });
    }
  }

  return (
    <Dialog maxWidth="lg" fullWidth onClose={onClose} open={open} {...other}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h4"
        >
          Add a LF Tag to Data All
        </Typography>
        <Typography align="center" color="textSecondary" variant="subtitle2">
            PLACEHOLDER DESCRIPTIONS
        </Typography>
          <Box sx={{ p: 3 }}>
            <Formik
              initialValues={{
                LFTagKey: '',
                LFTagValues: [],
                description: ''
              }}
              validationSchema={Yup.object().shape({
                LFTagKey: Yup.string()
                  .max(255)
                  .required('*LF Tag Name is required'),
                  LFTagValues: Yup.array()
                  .required('*List of LF Tag Values is required'),
                  description: Yup.string()
                  .max(255)
              })}
              onSubmit={async (
                values,
                { setErrors, setStatus, setSubmitting }
              ) => {
                await submit(values, setStatus, setSubmitting, setErrors);
              }}
            >
              {({
                errors,
                handleChange,
                handleSubmit,
                isSubmitting,
                setFieldValue,
                touched,
                values
              }) => (
                <form onSubmit={handleSubmit}>
                  <CardContent>
                    <TextField
                      error={Boolean(
                        touched.LFTagKey &&
                          errors.LFTagKey
                      )}
                      fullWidth
                      helperText={
                        touched.LFTagKey &&
                        errors.LFTagKey
                      }
                      label="LF Tag Name"
                      placeholder="Name for your Lake Formation Tag"
                      name="LFTagKey"
                      onChange={handleChange}
                      value={values.LFTagKey}
                      variant="outlined"
                    />
                  </CardContent>
                  <CardContent>
                    <ChipInput
                      error={Boolean(
                        touched.LFTagValues &&
                          errors.LFTagValues
                      )}
                      fullWidth
                      helperText={
                        touched.LFTagValues &&
                        errors.LFTagValues
                      }
                      label="LF Tag Values"
                      placeholder="Values for your Lake Formation Tag (Hit enter after typing value)"
                      onChange={(chip) => {
                        setFieldValue('LFTagValues', [...chip]);
                      }}
                      name="LFTagValues"
                      variant="outlined"
                    />
                  </CardContent>
                  <CardContent>
                    <TextField
                      error={Boolean(
                        touched.description &&
                          errors.description
                      )}
                      fullWidth
                      multiline
                      helperText={
                        touched.description &&
                        errors.description
                      }
                      label="LF Tag Description"
                      placeholder="Description of your Lake Formation Tag"
                      name="description"
                      onChange={handleChange}
                      value={values.description}
                      variant="outlined"
                    />
                  </CardContent>
                  <Box>
                    <CardContent>
                      <LoadingButton
                        fullWidth
                        startIcon={<GroupAddOutlined fontSize="small" />}
                        color="primary"
                        disabled={isSubmitting}
                        type="submit"
                        variant="contained"
                      >
                        Add LF Tag
                      </LoadingButton>
                    </CardContent>
                  </Box>
                </form>
              )}
            </Formik>
          </Box>
      </Box>
    </Dialog>
  );
};

LFTagAddForm.propTypes = {
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired,
  reloadTags: PropTypes.func
};

export default LFTagAddForm;
