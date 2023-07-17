import PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Grid,
  IconButton,
  InputAdornment,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import { DeleteOutlined, Warning } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import { useSnackbar } from 'notistack';
import { BsFolder } from 'react-icons/bs';
import useClient from '../../hooks/useClient';
import * as Defaults from '../../components/defaults';
import Scrollbar from '../../components/Scrollbar';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import SearchIcon from '../../icons/Search';
import PlusIcon from '../../icons/Plus';
import DeleteObjectModal from '../../components/DeleteObjectModal';
import removeDatasetFromCluster from '../../api/RedshiftCluster/removeDatasetFromCluster';
import WarehouseLoadDatasetModal from './WarehouseLoadDatasetModal';
import Pager from '../../components/Pager';
import listClusterDatasets from '../../api/RedshiftCluster/listClusterDatasets';
import WarehouseTables from './WarehouseTables';

const WarehouseDatasets = ({ warehouse }) => {
  const client = useClient();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const [items, setItems] = useState(Defaults.PagedResponseDefault);
  const [filter, setFilter] = useState(Defaults.DefaultFilter);
  const [loading, setLoading] = useState(null);
  const [inputValue, setInputValue] = useState('');
  const [isLoadDatasetsOpen, setIsLoadDatasetsOpen] = useState(false);
  const [isDeleteObjectModalOpen, setIsDeleteObjectModalOpen] = useState(false);
  const [datasetToDelete, setDatasetToDelete] = useState(null);
  const handleDeleteObjectModalOpen = (dataset) => {
    setDatasetToDelete(dataset);
    setIsDeleteObjectModalOpen(true);
  };
  const handleDeleteObjectModalClose = () => {
    setDatasetToDelete(null);
    setIsDeleteObjectModalOpen(false);
  };

  const fetchItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      listClusterDatasets({
        clusterUri: warehouse.clusterUri,
        filter: { ...filter }
      })
    );
    if (!response.errors) {
      setItems({ ...response.data.listRedshiftClusterDatasets });
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [warehouse.clusterUri, client, dispatch, filter]);

  const handleLoadDatasetsModalOpen = () => {
    setIsLoadDatasetsOpen(true);
  };

  const handleLoadDatasetsModalClose = () => {
    setIsLoadDatasetsOpen(false);
  };

  const unloadDataset = useCallback(async () => {
    const response = await client.mutate(
      removeDatasetFromCluster({
        clusterUri: warehouse.clusterUri,
        datasetUri: datasetToDelete.datasetUri
      })
    );
    if (!response.errors) {
      handleDeleteObjectModalClose();
      enqueueSnackbar('Dataset unloaded', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  }, [
    warehouse.clusterUri,
    enqueueSnackbar,
    fetchItems,
    dispatch,
    client,
    datasetToDelete
  ]);

  const handleInputChange = (event) => {
    setInputValue(event.target.value);
    setFilter({ ...filter, term: event.target.value });
  };

  const handleInputKeyup = (event) => {
    if (event.code === 'Enter') {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  };

  const handlePageChange = async (event, value) => {
    if (value <= items.pages && value !== items.page) {
      await setFilter({ ...filter, page: value });
    }
  };

  useEffect(() => {
    if (client) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, filter.page, fetchItems, dispatch]);

  return (
    <Box>
      <Card>
        <CardHeader
          action={
            <LoadingButton
              color="primary"
              onClick={handleLoadDatasetsModalOpen}
              startIcon={<PlusIcon fontSize="small" />}
              sx={{ m: 1 }}
              variant="outlined"
            >
              Load dataset
            </LoadingButton>
          }
          title={
            <Box>
              <BsFolder style={{ marginRight: '10px' }} />
              Loaded Datasets
            </Box>
          }
        />
        <Divider />
        <Box
          sx={{
            alignItems: 'center',
            display: 'flex',
            flexWrap: 'wrap',
            m: -1,
            p: 2
          }}
        >
          <Grid item md={10} sm={6} xs={12}>
            <Box
              sx={{
                m: 1,
                maxWidth: '100%',
                width: 500
              }}
            >
              <TextField
                fullWidth
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon fontSize="small" />
                    </InputAdornment>
                  )
                }}
                onChange={handleInputChange}
                onKeyUp={handleInputKeyup}
                placeholder="Search"
                value={inputValue}
                variant="outlined"
              />
            </Box>
          </Grid>
        </Box>
        <Scrollbar>
          <Box sx={{ minWidth: 600 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
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
                        <TableCell>{`s3://${dataset.S3BucketName}`}</TableCell>
                        <TableCell>{dataset.GlueDatabaseName}</TableCell>
                        <TableCell>
                          <IconButton
                            onClick={() => {
                              setDatasetToDelete(dataset);
                              handleDeleteObjectModalOpen(dataset);
                            }}
                          >
                            <DeleteOutlined fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow hover>
                      <TableCell>No datasets loaded to cluster.</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              )}
            </Table>
            {items.nodes.length > 0 && (
              <Pager
                mgTop={2}
                mgBottom={2}
                items={items}
                onChange={handlePageChange}
              />
            )}
          </Box>
        </Scrollbar>
      </Card>

      {isLoadDatasetsOpen && (
        <WarehouseLoadDatasetModal
          warehouse={warehouse}
          open={isLoadDatasetsOpen}
          reload={fetchItems}
          onApply={handleLoadDatasetsModalClose}
          onClose={handleLoadDatasetsModalClose}
        />
      )}

      {datasetToDelete && (
        <DeleteObjectModal
          objectName={datasetToDelete.label}
          onApply={handleDeleteObjectModalClose}
          onClose={handleDeleteObjectModalClose}
          open={isDeleteObjectModalOpen}
          deleteFunction={unloadDataset}
          deleteMessage={
            <Card>
              <CardContent>
                <Typography gutterBottom variant="body2">
                  <Warning /> Dataset Spectrum schema will be removed from the
                  cluster.
                </Typography>
              </CardContent>
            </Card>
          }
        />
      )}
      <Box sx={{ mt: 3 }}>
        <WarehouseTables warehouse={warehouse} />
      </Box>
    </Box>
  );
};

WarehouseDatasets.propTypes = {
  warehouse: PropTypes.object.isRequired
};

export default WarehouseDatasets;
