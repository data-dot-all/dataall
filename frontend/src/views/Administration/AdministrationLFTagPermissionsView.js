import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import * as BsIcons from 'react-icons/bs';
import {
  Box,
  Card,
  Button,
  CardHeader,
  Divider,
  Grid,
  InputAdornment,
  Table,
  Chip,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import { LoadingButton } from '@mui/lab';
import { useTheme } from '@mui/styles';
import useClient from '../../hooks/useClient';
import * as Defaults from '../../components/defaults';
import SearchIcon from '../../icons/Search';
import Scrollbar from '../../components/Scrollbar';
import RefreshTableMenu from '../../components/RefreshTableMenu';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import Pager from '../../components/Pager';
import listTenantLFTagPermissions from '../../api/LFTagPermissions/listTenantLFTagPermissions';
import { useSnackbar } from 'notistack';


const LFTagPermissionsView = () => {
  const client = useClient();
  const dispatch = useDispatch();
  const [lfTagPermissions, setLFTagPermissions] = useState(Defaults.PagedResponseDefault);
  const [filter, setFilter] = useState(Defaults.DefaultFilter);
  const [loading, setLoading] = useState(true);
  const [inputValue, setInputValue] = useState('');

  const fetchLFTagPermissions = useCallback(async () => {
    try {
      const response = await client.query(listTenantLFTagPermissions(filter));
      if (!response.errors) {
        setLFTagPermissions(response.data.listTenantLFTagPermissions);
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoading(false);
    }
  }, [client, dispatch, filter]);

  const handleInputChange = (event) => {
    setInputValue(event.target.value);
    setFilter({ ...filter, term: event.target.value });
  };

  const handleInputKeyup = (event) => {
    if (event.code === 'Enter') {
      fetchLFTagPermissions().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  };

  const handlePageChange = async (event, value) => {
    if (value <= lfTagPermissions.pages && value !== lfTagPermissions.page) {
      await setFilter({ ...filter, page: value });
    }
  };

  useEffect(() => {
    if (client) {
      fetchLFTagPermissions().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, filter.page, fetchLFTagPermissions, dispatch]);

  return (
    <Box>
      <Card>
        <CardHeader
          action={<RefreshTableMenu refresh={fetchLFTagPermissions} />}
          title={
            <Box>
              <BsIcons.BsPeople style={{ marginRight: '10px' }} /> Tenant LF Tags
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
                  <TableCell>TagName</TableCell>
                  <TableCell>TagValues</TableCell>
                  <TableCell>AWS Account</TableCell>
                  <TableCell>Environment</TableCell>
                  <TableCell>Team</TableCell>
                </TableRow>
              </TableHead>
              {loading ? (
                <CircularProgress sx={{ mt: 1 }} />
              ) : (
                <TableBody>
                  {lfTagPermissions.nodes.length > 0 ? (
                    lfTagPermissions.nodes.map((tagPermission) => (
                      <TableRow hover>
                        <TableCell>{tagPermission.tagKey} </TableCell>
                        <TableCell>{tagPermission.tagValues} </TableCell>
                        <TableCell>{tagPermission.awsAccount} </TableCell>
                        <TableCell>{tagPermission.environmentLabel} </TableCell>
                        <TableCell>{tagPermission.SamlGroupName} </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow hover>
                      <TableCell>No LF Tag Permissions Created</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              )}
            </Table>
            {!loading && lfTagPermissions.nodes.length > 0 && (
              <Pager
                mgTop={2}
                mgBottom={2}
                items={lfTagPermissions}
                onChange={handlePageChange}
              />
            )}
          </Box>
        </Scrollbar>
      </Card>
    </Box>
  );
};

LFTagPermissionsView.propTypes = {};

export default LFTagPermissionsView;
