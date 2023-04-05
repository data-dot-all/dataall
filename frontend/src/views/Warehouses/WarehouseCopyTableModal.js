import { CopyAll } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import {
  Box,
  CardContent,
  Dialog,
  FormHelperText,
  MenuItem,
  TextField,
  Typography
} from '@mui/material';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';
import * as Yup from 'yup';
import { copyTableToCluster, listAvailableDatasetTables } from '../../api';
import { Defaults } from '../../components';
import { SET_ERROR, useDispatch } from '../../globalErrors';
import { useClient } from '../../hooks';

const WarehouseCopyTableModal = (props) => {
  const client = useClient();
  const { warehouse, onApply, onClose, open, reload, ...other } = props;
  const { enqueueSnackbar } = useSnackbar();
  const [filter] = useState(Defaults.selectListFilter);
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [itemOptions, setItemOptions] = useState([]);
  const [selectedTable, setSelectedTable] = useState('');
  const dispatch = useDispatch();
  const [loading, setLoading] = useState(true);

  const fetchItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      listAvailableDatasetTables({
        clusterUri: warehouse.clusterUri,
        filter
      })
    );
    if (!response.errors) {
      setItems({ ...response.data.listRedshiftClusterAvailableDatasetTables });
      setItemOptions(
        response.data.listRedshiftClusterAvailableDatasetTables.nodes.map(
          (e) => ({ ...e, value: e, label: e.label })
        )
      );
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, warehouse.clusterUri, filter]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const input = {
        clusterUri: warehouse.clusterUri,
        datasetUri: values.table.datasetUri,
        tableUri: values.table.tableUri,
        schema: values.schema,
        dataLocation: values.dataLocation || null
      };
      const response = await client.mutate(copyTableToCluster(input));
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Table copy started', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        if (reload) {
          reload();
        }
        if (onApply) {
          onApply();
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

  useEffect(() => {
    if (client) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, fetchItems, dispatch]);

  if (!warehouse) {
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
          Copy a table to cluster {warehouse.label}
        </Typography>
        <Typography align="center" color="textSecondary" variant="subtitle2">
          <p>
            You can specify the target schema and the S3 data location for the
            copy command. This copy will be done on cluster{' '}
            <b>{warehouse.name} </b>
            and database <b>{warehouse.databaseName}</b>
          </p>
        </Typography>
        {!loading && items && items.nodes.length <= 0 ? (
          <Typography color="textPrimary" variant="subtitle2">
            No tables found.
          </Typography>
        ) : (
          <Box sx={{ p: 3 }}>
            <Formik
              initialValues={{
                table: itemOptions[0],
                schema: '',
                dataLocation: ''
              }}
              validationSchema={Yup.object().shape({
                table: Yup.object().required('*Table is required'),
                schema: Yup.string().max(255).required('*Schema is required'),
                dataLocation: Yup.string().nullable()
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
                setFieldValue,
                isSubmitting,
                touched,
                values
              }) => (
                <form onSubmit={handleSubmit}>
                  <Box>
                    <CardContent>
                      <TextField
                        error={Boolean(touched.schema && errors.schema)}
                        fullWidth
                        helperText={touched.schema && errors.schema}
                        label="Schema"
                        name="schema"
                        onBlur={handleBlur}
                        onChange={handleChange}
                        value={values.schema}
                        variant="outlined"
                      />
                    </CardContent>
                    <CardContent>
                      <TextField
                        error={Boolean(touched.table && errors.table)}
                        helperText={touched.table && errors.table}
                        fullWidth
                        label="Table"
                        name="table"
                        onChange={(event) => {
                          setFieldValue('table', event.target.value);
                          setSelectedTable(
                            `(s3://${event.target.value.dataset.S3BucketName}/)`
                          );
                        }}
                        select
                        value={values.table}
                        variant="outlined"
                      >
                        {itemOptions.map((table) => (
                          <MenuItem key={table.value} value={table.value}>
                            {table.label}
                          </MenuItem>
                        ))}
                      </TextField>
                    </CardContent>
                    <CardContent>
                      <TextField
                        error={Boolean(
                          touched.dataLocation && errors.dataLocation
                        )}
                        fullWidth
                        helperText={touched.dataLocation && errors.dataLocation}
                        label={`S3 Prefix ${selectedTable}`}
                        name="dataLocation"
                        onBlur={handleBlur}
                        onChange={handleChange}
                        value={values.dataLocation}
                        variant="outlined"
                      />
                    </CardContent>
                  </Box>
                  {errors.submit && (
                    <Box sx={{ mt: 3 }}>
                      <FormHelperText error>{errors.submit}</FormHelperText>
                    </Box>
                  )}
                  <CardContent>
                    <LoadingButton
                      fullWidth
                      startIcon={<CopyAll size={15} />}
                      color="primary"
                      disabled={isSubmitting}
                      type="submit"
                      variant="contained"
                    >
                      Copy table
                    </LoadingButton>
                  </CardContent>
                </form>
              )}
            </Formik>
          </Box>
        )}
      </Box>
    </Dialog>
  );
};

WarehouseCopyTableModal.propTypes = {
  warehouse: PropTypes.object.isRequired,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  reload: PropTypes.func,
  open: PropTypes.bool.isRequired
};

export default WarehouseCopyTableModal;
