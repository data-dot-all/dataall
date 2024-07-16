import { GroupAddOutlined } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import {
  Autocomplete,
  Box,
  CardContent,
  CircularProgress,
  Dialog,
  Divider,
  Grid,
  MenuItem,
  TextField,
  Typography
} from '@mui/material';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import React from 'react';
import * as Yup from 'yup';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient, useFetchGroups } from 'services';
import { createTableDataFilter } from '../services';

export const TableDataFilterAddForm = (props) => {
  const { table, onClose, open, reload, ...other } = props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();

  const dataFilterOptions = ['ROW', 'COLUMN'];

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        createTableDataFilter({
          filterName: values.filterName,
          SamlGroupName: values.SamlAdminGroupName,
          tableUri: table.tableUri,
          filterType: values.filterType,
          includedCols: values.includedCols,
          rowExpression: values.rowExpression,
          description: values.description
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Data filter created for table', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        if (reload) {
          reload();
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

  if (!table) {
    return null;
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
          Add a new data filter for table {table.label}
        </Typography>
        <Typography align="center" color="textSecondary" variant="subtitle2">
          Data filters allow you to restrict access to a table in data.all. They
          are owned by the dataset owners and can be applied on data shares in
          the data.all UI. Each data filter is specific to a particular table.
        </Typography>
        <Box sx={{ p: 3 }}>
          <Formik
            initialValues={{
              filterName: '',
              description: '',
              filterType: '',
              includedCols: '',
              rowExpression: ''
            }}
            validationSchema={Yup.object().shape({
              filterName: Yup.string()
                .max(255)
                .required('*Connection Name is required'),
              filterType: Yup.string()
                .max(255)
                .required('*Filter Type is required'),
              includedCols: Yup.string().max(255),
              rowExpression: Yup.string().max(255),
              description: Yup.string().max(255)
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
                <Box>
                  <CardContent>
                    <TextField
                      error={Boolean(touched.filterName && errors.filterName)}
                      fullWidth
                      helperText={touched.filterName && errors.filterName}
                      label="Filter Name"
                      placeholder="Name to identify your Data Filter in data.all"
                      name="filterName"
                      onChange={handleChange}
                      value={values.filterName}
                      variant="outlined"
                    />
                  </CardContent>
                  <CardContent>
                    <TextField
                      error={Boolean(touched.description && errors.description)}
                      fullWidth
                      helperText={touched.description && errors.description}
                      label="Data Filter Description"
                      placeholder="Description of Data Filter"
                      name="description"
                      onChange={handleChange}
                      value={values.description}
                      variant="outlined"
                    />
                  </CardContent>
                </Box>
                <Grid container spacing={3}>
                  <Grid item lg={6} md={6} xs={12}>
                    <CardContent>
                      <TextField
                        fullWidth
                        error={Boolean(touched.filterType && errors.filterType)}
                        helperText={touched.filterType && errors.filterType}
                        label="Filter Type"
                        name="filterType"
                        onChange={handleChange}
                        select
                        value={values.filterType}
                        variant="outlined"
                      >
                        {dataFilterOptions.map((option) => (
                          <MenuItem key={option} value={option}>
                            {option}
                          </MenuItem>
                        ))}
                      </TextField>
                    </CardContent>
                  </Grid>
                  <Grid item lg={6} md={6} xs={12}>
                    {values.filterType === 'ROW' && (
                      <Box>
                        <CardContent>
                          <TextField
                            error={Boolean(
                              touched.rowExpression && errors.rowExpression
                            )}
                            fullWidth
                            helperText={
                              touched.rowExpression && errors.rowExpression
                            }
                            label="Row Expression"
                            placeholder="Row Expression"
                            name="rowExpression"
                            onChange={handleChange}
                            value={values.rowExpression}
                            variant="outlined"
                          />
                        </CardContent>
                      </Box>
                    )}
                    {values.filterType === 'COLUMN' && (
                      <Box>
                        <CardContent>
                          <TextField
                            error={Boolean(
                              touched.includedCols && errors.includedCols
                            )}
                            fullWidth
                            helperText={
                              touched.includedCols && errors.includedCols
                            }
                            label="Cluster Id"
                            placeholder="Included Columns"
                            name="includedCols"
                            onChange={handleChange}
                            value={values.includedCols}
                            variant="outlined"
                          />
                        </CardContent>
                      </Box>
                    )}
                  </Grid>
                </Grid>
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
                      Add Data Filter
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

TableDataFilterAddForm.propTypes = {
  table: PropTypes.object.isRequired,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired,
  reload: PropTypes.func
};
