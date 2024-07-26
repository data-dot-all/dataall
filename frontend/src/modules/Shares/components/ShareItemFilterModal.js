import { LoadingButton } from '@mui/lab';
import {
  Box,
  CardContent,
  CardHeader,
  Dialog,
  FormHelperText,
  Typography,
  TextField
} from '@mui/material';
import { Formik } from 'formik';
import { DataGrid } from '@mui/x-data-grid';

import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import { Defaults } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import CircularProgress from '@mui/material/CircularProgress';
import { listTableDataFilters, useClient } from 'services';
import { updateShareItemFilters } from '../services';

export const ShareItemFilterModal = (props) => {
  const {
    item,
    itemDataFilter,
    onApply,
    onClose,
    open,
    reloadItems,
    ...other
  } = props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const [pageSize, setPageSize] = useState(5);
  const [selectionModel, setSelectionModel] = useState([]);
  const [selectionModelNames, setSelectionModelNames] = useState([]);

  const columns = [
    { field: 'id', hide: true },
    {
      field: 'label',
      headerName: 'Filter Name',
      flex: 1,
      // minWidth: 200,
      // resizable: true,
      editable: false
    },
    {
      field: 'description',
      headerName: 'Description',
      flex: 1,
      // minWidth: 400,
      // resizable: true,
      editable: false
    },
    {
      field: 'filterType',
      headerName: 'Filter Type',
      flex: 0.5,
      // minWidth: 100,
      // resizable: true,
      editable: false
    },
    {
      field: 'includedCols',
      headerName: 'Included Columns',
      flex: 2,
      // minWidth: 400,
      // resizable: true,
      editable: false
    },
    {
      field: 'rowExpression',
      headerName: 'Row Expression',
      flex: 2,
      // minWidth: 400,
      // resizable: true,
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
        updateShareItemFilters({
          shareItemUri: item.shareItemUri,
          label: values.label,
          filterUris: selectionModel,
          filterNames: selectionModelNames
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
      if (itemDataFilter) {
        setSelectionModel(itemDataFilter.dataFilterUris);
        setSelectionModelNames(itemDataFilter.dataFilterNames);
      }
      fetchFilters().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch, fetchFilters]);

  if (!item) {
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
              label: itemDataFilter?.label || '',
              filterUris: itemDataFilter?.dataFilterUris || []
            }}
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
                    <CardContent>
                      <TextField
                        error={Boolean(touched.label && errors.label)}
                        fullWidth
                        helperText={touched.label && errors.label}
                        label="Item Filter Name"
                        name="label"
                        onBlur={handleBlur}
                        onChange={handleChange}
                        value={values.label}
                        variant="outlined"
                      />
                    </CardContent>
                    <CardHeader fullWidth title="Select Data Filters" />
                    <Box fullWidth>
                      <DataGrid
                        fullWidth
                        autoHeight
                        scrollbarSize={50}
                        rowSpacingType="border"
                        rows={filters}
                        getRowId={(filter) => filter.filterUri}
                        columns={columns}
                        pageSize={pageSize}
                        rowsPerPageOptions={[5, 10, 20]}
                        onPageSizeChange={(newPageSize) =>
                          setPageSize(newPageSize)
                        }
                        checkboxSelection
                        onSelectionModelChange={(newSelection) => {
                          setSelectionModel(newSelection);
                          setSelectionModelNames(
                            newSelection.map((uri) => {
                              const filter = filters.find(
                                (filter) => filter.filterUri === uri
                              );
                              return filter.label;
                            })
                          );
                        }}
                        selectionModel={selectionModel}
                        loading={loading}
                      />
                    </Box>
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
  itemDataFilter: PropTypes.object,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  reloadItems: PropTypes.func,
  open: PropTypes.bool.isRequired
};
