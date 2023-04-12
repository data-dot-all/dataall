import {
  Box,
  Dialog,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';
import { Defaults, Pager, Scrollbar } from '../../components';
import { SET_ERROR, useDispatch } from '../../globalErrors';
import { PlusIcon } from '../../icons';
import {
  addDatasetToCluster,
  listAvailableDatasets,
  useClient
} from '../../services';

const WarehouseLoadDatasetModal = (props) => {
  const client = useClient();
  const { warehouse, onApply, onClose, open, reload, ...other } = props;
  const { enqueueSnackbar } = useSnackbar();
  const [filter, setFilter] = useState(Defaults.filter);
  const [items, setItems] = useState(Defaults.pagedResponse);
  const dispatch = useDispatch();
  const [loading, setLoading] = useState(true);

  const fetchItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      listAvailableDatasets({
        clusterUri: warehouse.clusterUri,
        filter: {
          ...filter
        }
      })
    );
    if (!response.errors) {
      setItems({ ...response.data.listRedshiftClusterAvailableDatasets });
      reload();
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [warehouse.clusterUri, client, dispatch, filter, reload]);

  const loadDataset = useCallback(
    async (dataset) => {
      const response = await client.mutate(
        addDatasetToCluster({
          clusterUri: warehouse.clusterUri,
          datasetUri: dataset.datasetUri
        })
      );
      if (!response.errors) {
        enqueueSnackbar('Dataset loading to cluster started', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        await fetchItems();
        reload(true);
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    },
    [
      client,
      dispatch,
      enqueueSnackbar,
      reload,
      warehouse.clusterUri,
      fetchItems
    ]
  );

  const handlePageChange = async (event, value) => {
    if (value <= items.pages && value !== items.page) {
      await setFilter({ ...filter, isShared: true, page: value });
    }
  };

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
          Load datasets to cluster {warehouse.label}
        </Typography>
        <Typography align="center" color="textSecondary" variant="subtitle2">
          Dataset will be loaded from Amazon S3 to Amazon Redshift using
          Redshift Spectrum
        </Typography>
        {!loading && items && items.nodes.length <= 0 ? (
          <Typography color="textPrimary" variant="subtitle2">
            No items to add.
          </Typography>
        ) : (
          <Scrollbar>
            <Box sx={{ minWidth: 600 }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>AWS Account</TableCell>
                    <TableCell>Region</TableCell>
                    <TableCell>S3 Bucket</TableCell>
                    <TableCell>Glue Database</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                {loading ? (
                  <CircularProgress sx={{ mt: 1 }} />
                ) : (
                  <TableBody>
                    {items.nodes.length > 0 ? (
                      items.nodes.map((dataset) => (
                        <TableRow hover key={dataset.datasetUri}>
                          <TableCell>{dataset.name}</TableCell>
                          <TableCell>{dataset.AwsAccountId}</TableCell>
                          <TableCell>{dataset.region}</TableCell>
                          <TableCell>
                            {`s3://${dataset.S3BucketName}`}
                          </TableCell>
                          <TableCell>{dataset.GlueDatabaseName}</TableCell>
                          <TableCell>
                            <IconButton
                              onClick={() => {
                                loadDataset(dataset);
                              }}
                            >
                              <PlusIcon fontSize="small" />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow hover>
                        <TableCell>No datasets found</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                )}
              </Table>
              <Pager
                mgTop={2}
                mgBottom={2}
                items={items}
                onChange={handlePageChange}
              />
            </Box>
          </Scrollbar>
        )}
      </Box>
    </Dialog>
  );
};

WarehouseLoadDatasetModal.propTypes = {
  warehouse: PropTypes.object.isRequired,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  reload: PropTypes.func,
  open: PropTypes.bool.isRequired
};

export default WarehouseLoadDatasetModal;
