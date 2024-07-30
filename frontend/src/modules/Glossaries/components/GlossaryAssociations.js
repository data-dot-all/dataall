import { BlockOutlined, CheckCircleOutlined } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import {
  Box,
  Card,
  CardHeader,
  Divider,
  Link,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Defaults, Pager, RefreshTableMenu, Scrollbar } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import {
  approveTermAssociation,
  dismissTermAssociation,
  listGlossaryAssociations
} from '../services';

export const GlossaryAssociations = ({ glossary }) => {
  const client = useClient();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const [approving, setApproving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);

  const fetchItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      listGlossaryAssociations({
        nodeUri: glossary.nodeUri,
        filter
      })
    );
    if (!response.errors) {
      setIsAdmin(
        ['Admin'].indexOf(response.data.getGlossary.userRoleForGlossary) !== -1
      );
      setItems(response.data.getGlossary.associations);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, filter, glossary]);

  const approveAssociation = async (linkUri) => {
    setApproving(true);
    const response = await client.mutate(approveTermAssociation(linkUri));
    if (!response.errors) {
      enqueueSnackbar('Term association approved', {
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
    setApproving(false);
  };
  const dismissAssociation = async (linkUri) => {
    setApproving(true);
    const response = await client.mutate(dismissTermAssociation(linkUri));
    if (!response.errors) {
      enqueueSnackbar('Term association dismissed', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'warning'
      });
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setApproving(false);
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
          action={<RefreshTableMenu refresh={fetchItems} />}
          title={<Box>Term Associations</Box>}
        />
        <Divider />
        <Scrollbar>
          <Box sx={{ minWidth: 600 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Term</TableCell>
                  <TableCell>Target Type</TableCell>
                  <TableCell>Target Name</TableCell>
                  <TableCell>Approval</TableCell>
                </TableRow>
              </TableHead>
              {loading ? (
                <CircularProgress sx={{ mt: 1 }} />
              ) : (
                <TableBody>
                  {items.nodes.length > 0 ? (
                    items.nodes.map((item) => (
                      <TableRow hover key={item.name}>
                        <TableCell>{item.term.label}</TableCell>
                        <TableCell>
                          {/* eslint-disable-next-line no-underscore-dangle */}
                          {item.targetType === 'Dataset' && (
                            <span>S3/Glue Dataset</span>
                          )}
                          {/* eslint-disable-next-line no-underscore-dangle */}
                          {item.targetType === 'DatasetTable' && (
                            <span>Glue Table</span>
                          )}
                          {/* eslint-disable-next-line no-underscore-dangle */}
                          {item.targetType === 'Folder' && <span>Folder</span>}
                          {item.targetType === 'Dashboard' && (
                            <span>Dashboard</span>
                          )}
                          {/* eslint-disable-next-line no-underscore-dangle */}
                          {item.targetType === 'RedshiftDataset' && (
                            <span>Redshift Dataset</span>
                          )}
                          {/* eslint-disable-next-line no-underscore-dangle */}
                          {item.targetType === 'RedshiftDatasetTable' && (
                            <span>Redshift Table</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {/* eslint-disable-next-line no-underscore-dangle */}
                          {item.targetType === 'Dataset' && (
                            <Link
                              underline="hover"
                              color="textPrimary"
                              component={RouterLink}
                              to={`/console/s3-datasets/${item.targetUri}`}
                              variant="subtitle2"
                            >
                              {item.target.label}
                            </Link>
                          )}
                          {/* eslint-disable-next-line no-underscore-dangle */}
                          {item.targetType === 'DatasetTable' && (
                            <Link
                              underline="hover"
                              color="textPrimary"
                              component={RouterLink}
                              to={`/console/s3-datasets/table/${item.targetUri}`}
                              variant="subtitle2"
                            >
                              {item.target.label}
                            </Link>
                          )}
                          {/* eslint-disable-next-line no-underscore-dangle */}
                          {item.targetType === 'Folder' && (
                            <Link
                              underline="hover"
                              color="textPrimary"
                              component={RouterLink}
                              to={`/console/s3-datasets/folder/${item.targetUri}`}
                              variant="subtitle2"
                            >
                              {item.target.label}
                            </Link>
                          )}
                          {/* eslint-disable-next-line no-underscore-dangle */}
                          {item.targetType === 'Dashboard' && (
                            <Link
                              underline="hover"
                              color="textPrimary"
                              component={RouterLink}
                              to={`/console/dashboards/${item.targetUri}`}
                              variant="subtitle2"
                            >
                              {item.target.label}
                            </Link>
                          )}
                          {/* eslint-disable-next-line no-underscore-dangle */}
                          {item.targetType === 'RedshiftDataset' && (
                            <Link
                              underline="hover"
                              color="textPrimary"
                              component={RouterLink}
                              to={`/console/redshift-datasets/${item.targetUri}`}
                              variant="subtitle2"
                            >
                              {item.target.label}
                            </Link>
                          )}
                          {/* eslint-disable-next-line no-underscore-dangle */}
                          {item.targetType === 'RedshiftDatasetTable' && (
                            <Link
                              underline="hover"
                              color="textPrimary"
                              component={RouterLink}
                              to={`/console/redshift-datasets/table/${item.targetUri}`}
                              variant="subtitle2"
                            >
                              {item.target.label}
                            </Link>
                          )}
                        </TableCell>
                        <TableCell>
                          {!item.approvedBySteward ? (
                            <LoadingButton
                              disabled={!isAdmin}
                              loading={approving}
                              color="success"
                              startIcon={<CheckCircleOutlined />}
                              onClick={() => {
                                approveAssociation(item.linkUri).catch((e) =>
                                  dispatch({
                                    type: SET_ERROR,
                                    error: e.message
                                  })
                                );
                              }}
                              type="button"
                              variant="outlined"
                            >
                              Approve
                            </LoadingButton>
                          ) : (
                            <LoadingButton
                              disabled={!isAdmin}
                              loading={approving}
                              color="error"
                              startIcon={<BlockOutlined />}
                              onClick={() => {
                                dismissAssociation(item.linkUri).catch((e) =>
                                  dispatch({
                                    type: SET_ERROR,
                                    error: e.message
                                  })
                                );
                              }}
                              type="button"
                              variant="outlined"
                            >
                              Reject
                            </LoadingButton>
                          )}
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow hover>
                      <TableCell>No glossary associations found</TableCell>
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

GlossaryAssociations.propTypes = {
  glossary: PropTypes.object.isRequired
};
