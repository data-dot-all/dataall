import { LoadingButton } from '@mui/lab';
import {
  Box,
  CardContent,
  Dialog,
  FormHelperText,
  Typography,
  TextField,
  Link
} from '@mui/material';
import { Formik } from 'formik';
import * as Yup from 'yup';
import { DataGrid } from '@mui/x-data-grid';
import { Link as RouterLink } from 'react-router-dom';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import { Defaults } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import CircularProgress from '@mui/material/CircularProgress';
import { listTableDataFilters, useClient } from 'services';
import {
  removeShareItemFilter,
  updateShareItemFilters,
  listTableDataFiltersByAttached
} from '../services';

export const ShareItemFilterModal = (props) => {
  const {
    item,
    shareUri,
    itemDataFilter,
    onApply,
    onClose,
    reloadItems,
    open,
    viewOnly,
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
  const [isRemoving, setRemoving] = useState(false);

  const [filters, setFilters] = useState([]);

  const fetchFilters = useCallback(async () => {
    try {
      setLoading(true);
      let response;
      if (viewOnly) {
        response = await client.query(
          listTableDataFiltersByAttached({
            attachedDataFilterUri:
              itemDataFilter?.attachedDataFilterUri || null,
            filter: Defaults.selectListFilter
          })
        );
      } else {
        response = await client.query(
          listTableDataFilters({
            tableUri: item.itemUri,
            filter: Defaults.selectListFilter
          })
        );
      }
      if (!response.errors) {
        if (viewOnly) {
          setFilters(response.data.listTableDataFiltersByAttached.nodes);
        } else {
          setFilters(response.data.listTableDataFilters.nodes);
        }
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

  const remove = async (attachedDataFilterUri) => {
    setRemoving(true);
    const response = await client.mutate(
      removeShareItemFilter({ attachedDataFilterUri: attachedDataFilterUri })
    );
    if (!response.errors) {
      enqueueSnackbar('Removed data filters from table item', {
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
    setRemoving(false);
  };

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

  if (viewOnly) {
    return (
      <Dialog maxWidth="lg" fullWidth onClose={onClose} open={open} {...other}>
        <Box fullWidth sx={{ p: 3 }}>
          <Typography
            align="center"
            color="textPrimary"
            gutterBottom
            variant="h4"
          >
            Data filters assigned to {item.itemName}
          </Typography>
          {loading ? (
            <CircularProgress sx={{ mt: 1 }} size={20} />
          ) : (
            <DataGrid
              fullWidth
              autoHeight
              scrollbarSize={50}
              rowSpacingType="border"
              rows={filters.filter((f) =>
                itemDataFilter.dataFilterUris.includes(f.filterUri)
              )}
              getRowId={(filter) => filter.filterUri}
              columns={columns}
              pageSize={pageSize}
              rowsPerPageOptions={[5, 10, 20]}
              onPageSizeChange={(newPageSize) => setPageSize(newPageSize)}
              loading={loading}
            />
          )}
        </Box>
      </Dialog>
    );
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
          Assign data filters to {item.itemName}
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
            validationSchema={Yup.object().shape({
              label: Yup.string().max(255).required('*Value is required')
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
                    <Link
                      underline="hover"
                      component={RouterLink}
                      to={`/console/s3-datasets/table/${item.itemUri}`}
                      state={{ shareUri: shareUri, tab: 'datafilters' }}
                      variant="subtitle2"
                    >
                      Create New Data Filters
                    </Link>
                    <Box fullWidth>
                      <DataGrid
                        sx={{
                          wordWrap: 'break-word', //TODO: create a generic styled datagrid to be used across features
                          '& .MuiDataGrid-row': {
                            borderBottom: '1px solid rgba(145, 158, 171, 0.24)'
                          },
                          '& .MuiDataGrid-columnHeaders': {
                            borderBottom: 0.5
                          },
                          '&.MuiDataGrid-root--densityStandard .MuiDataGrid-cell':
                            {
                              py: '15px'
                            }
                          // '& .MuiDataGrid-cell:hover': {
                          //   color: theme.palette.primary.main
                          // },
                        }}
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
                        <LoadingButton
                          loading={isRemoving}
                          disabled={!item?.attachedDataFilterUri}
                          color="primary"
                          sx={{ ml: 1 }}
                          onClick={() => remove(item.attachedDataFilterUri)}
                          type="button"
                          variant="outlined"
                        >
                          Remove Filter(s)
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
  shareUri: PropTypes.string,
  itemDataFilter: PropTypes.object,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  reloadItems: PropTypes.func,
  open: PropTypes.bool.isRequired,
  viewOnly: PropTypes.bool
};
