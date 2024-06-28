//import { DeleteOutlined, SyncAlt, Warning } from '@mui/icons-material';
// import { SyncAlt } from '@mui/icons-material';
// import { LoadingButton } from '@mui/lab';
import {
  Box,
  Card,
  //CardContent,
  CardHeader,
  Divider,
  Grid,
  IconButton,
  InputAdornment,
  Link,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField
  //Typography
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
// import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import { BsTable } from 'react-icons/bs';
import { useNavigate } from 'react-router';
import { Link as RouterLink } from 'react-router-dom';
import {
  ArrowRightIcon,
  Defaults,
  //DeleteObjectModal,
  Pager,
  RefreshTableMenu,
  Scrollbar,
  SearchIcon
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';

import { listRedshiftDatasetTables } from '../services';

export const RedshiftDatasetTables = (props) => {
  const { dataset } = props;
  const client = useClient();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  //const { enqueueSnackbar } = useSnackbar();
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const [loading, setLoading] = useState(null);
  const [inputValue, setInputValue] = useState('');
  // const [isDeleteObjectModalOpen, setIsDeleteObjectModalOpen] = useState(false);
  // const [tableToDelete, setTableToDelete] = useState(null);

  // const handleDeleteObjectModalOpen = (table) => {
  //   setTableToDelete(table);
  //   setIsDeleteObjectModalOpen(true);
  // };
  // const handleDeleteObjectModalClose = () => {
  //   setTableToDelete(null);
  //   setIsDeleteObjectModalOpen(false);
  // };

  const fetchItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      listRedshiftDatasetTables({
        datasetUri: dataset.datasetUri,
        filter: { ...filter }
      })
    );
    if (!response.errors) {
      setItems({ ...response.data.listRedshiftDatasetTables });
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [dispatch, client, dataset, filter]);

  // const deleteTable = async () => {
  //   const response = await client.mutate(
  //     deleteDatasetTable({ tableUri: tableToDelete.tableUri })
  //   );
  //   if (!response.errors) {
  //     handleDeleteObjectModalClose();
  //     enqueueSnackbar('Table deleted', {
  //       anchorOrigin: {
  //         horizontal: 'right',
  //         vertical: 'top'
  //       },
  //       variant: 'success'
  //     });
  //     fetchItems().catch((e) =>
  //       dispatch({ type: SET_ERROR, error: e.message })
  //     );
  //   } else {
  //     dispatch({ type: SET_ERROR, error: response.errors[0].message });
  //   }
  // };

  useEffect(() => {
    if (client) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, filter.page, dispatch, fetchItems]);

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

  return (
    <Box>
      <Card>
        <CardHeader
          action={<RefreshTableMenu refresh={fetchItems} />}
          title={
            <Box>
              <BsTable style={{ marginRight: '10px' }} />
              Tables
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
          <Grid item md={9} sm={6} xs={12}>
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
                  <TableCell>Database</TableCell>
                  <TableCell>Location</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              {loading ? (
                <CircularProgress sx={{ mt: 1 }} />
              ) : (
                <TableBody>
                  {items.nodes.length > 0 ? (
                    items.nodes.map((table) => (
                      <TableRow hover key={table.tableUri}>
                        <TableCell>
                          <Link
                            underline="hover"
                            color="textPrimary"
                            component={RouterLink}
                            to={`/console/redshift-datasets/table/${table.tableUri}`}
                            variant="subtitle2"
                          >
                            {table.GlueTableName}
                          </Link>
                        </TableCell>
                        <TableCell>{table.GlueDatabaseName}</TableCell>
                        <TableCell>{table.S3Prefix}</TableCell>
                        <TableCell>
                          {/*{isAdmin && (*/}
                          {/*  <IconButton*/}
                          {/*    onClick={() => {*/}
                          {/*      setTableToDelete(table);*/}
                          {/*      handleDeleteObjectModalOpen(table);*/}
                          {/*    }}*/}
                          {/*  >*/}
                          {/*    <DeleteOutlined fontSize="small" />*/}
                          {/*  </IconButton>*/}
                          {/*)}*/}
                          <IconButton
                            onClick={() => {
                              navigate(
                                `/console/redshift-datasets/table/${table.tableUri}`
                              );
                            }}
                          >
                            <ArrowRightIcon fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow hover>
                      <TableCell>No tables found</TableCell>
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
    </Box>
  );
};

RedshiftDatasetTables.propTypes = {
  dataset: PropTypes.object.isRequired,
  isAdmin: PropTypes.bool.isRequired
};
