import PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';
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
import { BlockOutlined, CheckCircleOutlined } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import { Link as RouterLink } from 'react-router-dom';
import useClient from '../../hooks/useClient';
import * as Defaults from '../../components/defaults';
import Scrollbar from '../../components/Scrollbar';
import RefreshTableMenu from '../../components/RefreshTableMenu';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import listGlossaryAssociations from '../../api/Glossary/listGlossaryAssociations';
import approveTermAssociation from '../../api/Glossary/approveTermAssociation';
import dismissTermAssociation from '../../api/Glossary/dismissTermAssociation';
import Pager from '../../components/Pager';
import useAuth from '../../hooks/useAuth';

const GlossaryAssociations = ({ glossary }) => {
  const client = useClient();
  const dispatch = useDispatch();
  const { user } = useAuth();
  const { enqueueSnackbar } = useSnackbar();
  const [items, setItems] = useState(Defaults.PagedResponseDefault);
  const [filter, setFilter] = useState(Defaults.DefaultFilter);
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
        ['Admin'].indexOf(
          response.data.getGlossary.userRoleForGlossary
        ) !== -1
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
                          {item.target.__typename === 'Dataset' && (
                            <span>Dataset</span>
                          )}
                          {/* eslint-disable-next-line no-underscore-dangle */}
                          {item.target.__typename === 'DatasetTable' && (
                            <span>Table</span>
                          )}
                          {/* eslint-disable-next-line no-underscore-dangle */}
                          {item.target.__typename ===
                            'DatasetStorageLocation' && <span>Folder</span>}
                          {item.target.__typename === 'Dashboard' && (
                            <span>Dashboard</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {/* eslint-disable-next-line no-underscore-dangle */}
                          {item.target.__typename === 'Dataset' && (
                            <Link
                              underline="hover"
                              color="textPrimary"
                              component={RouterLink}
                              to={`/datasets/${item.targetUri}`}
                              variant="subtitle2"
                            >
                              {item.target.label}
                            </Link>
                          )}
                          {/* eslint-disable-next-line no-underscore-dangle */}
                          {item.target.__typename === 'DatasetTable' && (
                            <Link
                              underline="hover"
                              color="textPrimary"
                              component={RouterLink}
                              to={`/datasets/table/${item.targetUri}`}
                              variant="subtitle2"
                            >
                              {item.target.label}
                            </Link>
                          )}
                          {/* eslint-disable-next-line no-underscore-dangle */}
                          {item.target.__typename ===
                            'DatasetStorageLocation' && (
                            <Link
                              underline="hover"
                              color="textPrimary"
                              component={RouterLink}
                              to={`/datasets/folder/${item.targetUri}`}
                              variant="subtitle2"
                            >
                              {item.target.label}
                            </Link>
                          )}
                          {/* eslint-disable-next-line no-underscore-dangle */}
                          {item.target.__typename === 'Dashboard' && (
                            <Link
                              underline="hover"
                              color="textPrimary"
                              component={RouterLink}
                              to={`/dashboards/${item.targetUri}`}
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

export default GlossaryAssociations;
