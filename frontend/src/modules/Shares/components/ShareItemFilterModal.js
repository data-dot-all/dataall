import { LoadingButton } from '@mui/lab';
import {
  Box,
  CardContent,
  CardHeader,
  Dialog,
  FormHelperText,
  Typography
} from '@mui/material';
import { Formik } from 'formik';
import { DataGrid } from '@mui/x-data-grid';

import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import * as Yup from 'yup';
import { Defaults, Scrollbar } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import CircularProgress from '@mui/material/CircularProgress';
import { listTableDataFilters, useClient } from 'services';
import { updateFiltersTableShareItem } from '../services';

export const ShareItemFilterModal = (props) => {
  const { item, onApply, onClose, open, reloadItems, ...other } = props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const [pageSize, setPageSize] = useState(5);

  const columns = [
    { field: 'id', hide: true },
    {
      field: 'label',
      headerName: 'Filter Name',
      flex: 1,
      editable: false
    },
    {
      field: 'description',
      headerName: 'Description',
      flex: 1,
      editable: false
    },
    {
      field: 'filterType',
      headerName: 'Filter Type',
      flex: 0.5,
      editable: false
    },
    {
      field: 'includedCols',
      headerName: 'Included Columns',
      flex: 2,
      editable: false
    },
    {
      field: 'rowExpression',
      headerName: 'Row Expression',
      flex: 2,
      editable: false
    }
  ];

  const [loading, setLoading] = useState(false);

  const [filters, setFilters] = useState([]);

  const fetchFilters = useCallback(async () => {
    try {
      setLoading(true);

      const response = await client.query(
        listTableDataFilters({
          tableUri: item.itemUri,
          filter: Defaults.selectListFilter
        })
      );
      if (!response.errors) {
        setFilters(response.data.listTableDataFilters.nodes);
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoading(false);
    }
  }, [client, dispatch, item.shareItemUri]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        updateFiltersTableShareItem({
          shareItemUri: item.shareItemUri,
          filterUris: values.filterUris
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Filters added', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        if (reloadItems) {
          reloadItems();
        }
        if (onApply) {
          onApply();
        }
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (err) {
      setStatus({ success: false });
      setErrors({ submit: err.message });
      setSubmitting(false);
      dispatch({ type: SET_ERROR, error: err.message });
    }
  }

  useEffect(() => {
    if (client) {
      fetchFilters().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch, fetchFilters]);

  if (!item) {
    return null;
  }

  return (
    <Dialog maxWidth="md" fullWidth onClose={onClose} open={open} {...other}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h4"
        >
          Assign data filters to a table share item {item.itemName}
        </Typography>
        <Typography align="center" color="textSecondary" variant="subtitle2">
          Data filters allow data.all share approvers to restrict data access by
          column and/or row level access. NOTE: Adding more than 1 filter will
          be the <b>intersection</b> of all filters (logical AND operator)
        </Typography>
        <Box sx={{ p: 3 }}>
          <Formik
            initialValues={{
              filterUris: item.filterUris || []
            }}
            validationSchema={Yup.object().shape({
              filterUris: Yup.array().min(1).required()
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
              handleBlur,
              handleChange,
              handleSubmit,
              isSubmitting,
              setFieldValue,
              touched,
              values
            }) => (
              <form onSubmit={handleSubmit}>
                {loading ? (
                  <CircularProgress sx={{ mt: 1 }} size={20} />
                ) : (
                  <>
                    <CardHeader fullWidth title="Select Data Filters" />
                    <Scrollbar>
                      <Box fullWidth>
                        <DataGrid
                          fullWidth
                          autoHeight
                          rowSpacingType="border"
                          autosizeOptions={{
                            columns: ['rowExpression', 'includedCols'],
                            includeOutliers: true,
                            includeHeaders: true
                          }}
                          rows={filters}
                          getRowId={(filter) => filter.filterUri}
                          columns={columns}
                          pageSize={pageSize}
                          rowsPerPageOptions={[5, 10, 20]}
                          onPageSizeChange={(newPageSize) =>
                            setPageSize(newPageSize)
                          }
                          checkboxSelection
                          rowSelectionModel={item.filterUris || []}
                          onSelectionModelChange={(newSelection) => {
                            setFieldValue('filterUris', newSelection);
                          }}
                          // selectionModel={values.filterUris}
                          loading={loading}
                        />
                      </Box>
                    </Scrollbar>

                    {/* <CardContent fullWidth>
                            <Autocomplete
                              multiple
                              id="tags-filled"
                              options={filters}
                              getOptionLabel={(opt) => `${opt.label} (${opt.description})`}
                              onChange={(event, value) => {
                                setFieldValue('filterUris', value);
                              }}
                              renderTags={(tagValue, getTagProps) =>
                                tagValue.map((option, index) => (
                                  <Chip
                                    label={option.label}
                                    {...getTagProps({ index })}
                                  />
                                ))
                              }
                              renderInput={(p) => (
                                <TextField
                                  {...p}
                                  variant="outlined"
                                  label="Data Filters"
                                  error={Boolean(
                                    touched.filterUris && errors.filterUris
                                  )}
                                  helperText={touched.filterUris && errors.filterUris}
                                />
                              )}
                            />
                          {/* <ChipInput
                            error={Boolean(touched.tags && errors.tags)}
                            fullWidth
                            helperText={touched.tags && errors.tags}
                            variant="outlined"
                            label="Data Filters"
                            placeholder="Hit enter after typing value"
                            onChange={(chip) => {
                              setFieldValue('filterUris', [...chip]);
                            }}
                          /> 
                        </CardContent> */}
                    {errors.submit && (
                      <Box sx={{ mt: 3 }}>
                        <FormHelperText error>{errors.submit}</FormHelperText>
                      </Box>
                    )}
                    <Box>
                      <CardContent>
                        <LoadingButton
                          color="primary"
                          disabled={isSubmitting}
                          type="submit"
                          variant="contained"
                        >
                          Assign Filters
                        </LoadingButton>
                      </CardContent>
                    </Box>
                  </>
                )}
              </form>
            )}
          </Formik>
        </Box>
      </Box>
    </Dialog>
  );
};

ShareItemFilterModal.propTypes = {
  item: PropTypes.object.isRequired,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  reloadItems: PropTypes.func,
  open: PropTypes.bool.isRequired
};
