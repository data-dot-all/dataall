import PropTypes from 'prop-types';
import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Grid,
  IconButton,
  InputAdornment, Link,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography
} from '@material-ui/core';
import CircularProgress from '@material-ui/core/CircularProgress';
import { DeleteOutlined, Warning } from '@material-ui/icons';
import { LoadingButton } from '@material-ui/lab';
import { useSnackbar } from 'notistack';
import { BsFolder } from 'react-icons/all';
import { useNavigate } from 'react-router';
import { Link as RouterLink } from 'react-router-dom';
import useClient from '../../hooks/useClient';
import * as Defaults from '../../components/defaults';
import Scrollbar from '../../components/Scrollbar';
import RefreshTableMenu from '../../components/RefreshTableMenu';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import listDatasetStorageLocations from '../../api/Dataset/listDatasetStorageLocations';
import FolderCreateModal from '../Folders/FolderCreateModal';
import SearchIcon from '../../icons/Search';
import PlusIcon from '../../icons/Plus';
import DeleteObjectModal from '../../components/DeleteObjectModal';
import removeDatasetStorageLocation from '../../api/Dataset/removeDatasetStorageLocation';
import ArrowRightIcon from '../../icons/ArrowRight';
import Pager from '../../components/Pager';

const DatasetFolders = ({ dataset, isAdmin }) => {
  const client = useClient();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const [items, setItems] = useState(Defaults.PagedResponseDefault);
  const [filter, setFilter] = useState(Defaults.DefaultFilter);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(null);
  const [isFolderCreateOpen, setIsFolderCreateOpen] = useState(false);
  const [isDeleteObjectModalOpen, setIsDeleteObjectModalOpen] = useState(false);
  const [folderToDelete, setFolderToDelete] = useState(null);
  const handleDeleteObjectModalOpen = (folder) => {
    setFolderToDelete(folder);
    setIsDeleteObjectModalOpen(true);
  };
  const handleDeleteObjectModalClose = () => {
    setFolderToDelete(null);
    setIsDeleteObjectModalOpen(false);
  };

  const fetchItems = async () => {
    setLoading(true);
    const response = await client.query(listDatasetStorageLocations(dataset.datasetUri, filter));
    if (!response.errors) {
      setItems({ ...response.data.getDataset.locations });
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  };

  const handleFolderCreateModalOpen = () => {
    setIsFolderCreateOpen(true);
  };

  const handleFolderCreateModalClose = () => {
    setIsFolderCreateOpen(false);
  };

  const handleInputChange = (event) => {
    setInputValue(event.target.value);
    setFilter({ ...filter, term: event.target.value });
  };

  const handleInputKeyup = (event) => {
    if ((event.code === 'Enter')) {
      fetchItems().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  };

  const handlePageChange = async (event, value) => {
    if (value <= items.pages && value !== items.page) {
      await setFilter({ ...filter, page: value });
    }
  };

  const deleteFolder = async () => {
    const response = await client.mutate(removeDatasetStorageLocation({ locationUri: folderToDelete.locationUri }));
    if (!response.errors) {
      handleDeleteObjectModalClose();
      enqueueSnackbar('Folder deleted', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      fetchItems().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  useEffect(() => {
    if (client) {
      fetchItems().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client]);

  return (
    <Box>
      <Card>
        <CardHeader
          action={<RefreshTableMenu refresh={fetchItems} />}
          title={(
            <Box>
              <BsFolder style={{ marginRight: '10px' }} />
              Folders
            </Box>
                    )}
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
          <Grid
            item
            md={10}
            sm={6}
            xs={12}
          >
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
          {isAdmin && (
          <Grid
            item
            md={2}
            sm={6}
            xs={12}
          >
            <LoadingButton
              color="primary"
              onClick={handleFolderCreateModalOpen}
              startIcon={<PlusIcon fontSize="small" />}
              sx={{ m: 1 }}
              variant="outlined"
            >
              Create
            </LoadingButton>
          </Grid>
          )}
        </Box>
        <Scrollbar>
          <Box sx={{ minWidth: 600 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>
                    Name
                  </TableCell>
                  <TableCell>
                    S3 Location
                  </TableCell>
                  <TableCell>
                    Description
                  </TableCell>
                  {isAdmin && (
                  <TableCell>
                    Actions
                  </TableCell>
                  )}
                </TableRow>
              </TableHead>
              {loading ? <CircularProgress sx={{ mt: 1 }} /> : (
                <TableBody>
                  {items.nodes.length > 0 ? items.nodes.map((folder) => (
                    <TableRow
                      hover
                      key={folder.locationUri}
                    >
                      <TableCell>
                        <Link
                          color="textPrimary"
                          component={RouterLink}
                          to={`/console/datasets/folder/${folder.locationUri}`}
                          variant="subtitle2"
                        >
                          {folder.name}
                        </Link>
                      </TableCell>
                      <TableCell>
                        {`s3://${dataset.S3BucketName}/${folder.S3Prefix}`}
                      </TableCell>
                      <TableCell>
                        {folder.description}
                      </TableCell>
                      <TableCell>
                        {isAdmin && (
                        <IconButton onClick={() => { setFolderToDelete(folder); handleDeleteObjectModalOpen(folder); }}>
                          <DeleteOutlined fontSize="small" />
                        </IconButton>
                        )}
                        <IconButton onClick={() => { navigate(`/console/datasets/folder/${folder.locationUri}`); }}>
                          <ArrowRightIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  )) : (
                    <TableRow
                      hover
                    >
                      <TableCell>
                        No folders found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              )}
            </Table>
            {!loading && items.nodes.length > 0 && (
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
      {isAdmin && (
      <FolderCreateModal
        dataset={dataset}
        onApply={handleFolderCreateModalClose}
        onClose={handleFolderCreateModalClose}
        reloadFolders={fetchItems}
        open={isFolderCreateOpen}
      />
      )}
      {isAdmin && folderToDelete && (
      <DeleteObjectModal
        objectName={folderToDelete.S3Prefix}
        onApply={handleDeleteObjectModalClose}
        onClose={handleDeleteObjectModalClose}
        open={isDeleteObjectModalOpen}
        deleteFunction={deleteFolder}
        deleteMessage={(
          <Card>
            <CardContent>
              <Typography
                gutterBottom
                variant="body2"
              >
                <Warning />
                {' '}
                Folder will be deleted from data.all catalog, but will still be available on Amazon S3 bucket.
              </Typography>
            </CardContent>
          </Card>
              )}
      />
      )}
    </Box>
  );
};

DatasetFolders.propTypes = {
  dataset: PropTypes.object.isRequired,
  isAdmin: PropTypes.bool.isRequired
};

export default DatasetFolders;
