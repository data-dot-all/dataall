import { Link } from '@mui/icons-material';
import {
  Box,
  Button,
  Card,
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
  TextField
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import { FaAws } from 'react-icons/fa';
import { useNavigate } from 'react-router';
import { Link as RouterLink } from 'react-router-dom';
import {
  ArrowRightIcon,
  Defaults,
  Pager,
  RefreshTableMenu,
  Scrollbar,
  SearchIcon,
  StackStatus
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { listOrganizationEnvironments } from '../services';

export const OrganizationEnvironments = (props) => {
  const { organization, ...other } = props;
  const client = useClient();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const [loading, setLoading] = useState(null);
  const [inputValue, setInputValue] = useState('');

  const fetchItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      listOrganizationEnvironments({
        filter,
        organizationUri: organization.organizationUri
      })
    );
    if (!response.errors) {
      setItems({ ...response.data.getOrganization.environments });
    }
    setLoading(false);
  }, [client, organization.organizationUri, filter]);

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
      fetchItems();
    }
  };

  const handlePageChange = async (event, value) => {
    if (value <= items.pages && value !== items.page) {
      await setFilter({ ...filter, page: value });
    }
  };

  return (
    <Card {...other}>
      <CardHeader
        action={<RefreshTableMenu refresh={fetchItems} />}
        title={
          <Box>
            <FaAws style={{ marginRight: '10px' }} /> Environments
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
              placeholder="Search environments"
              value={inputValue}
              variant="outlined"
            />
          </Box>
        </Grid>
        <Grid item md={2} sm={6} xs={12}>
          <Button
            color="primary"
            component={RouterLink}
            startIcon={<Link fontSize="small" />}
            sx={{ m: 1 }}
            variant="contained"
            to={`/console/organizations/${organization.organizationUri}/link`}
          >
            Link Environment
          </Button>
        </Grid>
      </Box>
      <Scrollbar>
        <Box sx={{ minWidth: 600 }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>AWS Account</TableCell>
                <TableCell>Region</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            {loading ? (
              <CircularProgress sx={{ mt: 1 }} size={20} />
            ) : (
              <TableBody>
                {items.nodes.length > 0 ? (
                  items.nodes.map((env) => (
                    <TableRow hover key={env.environmentUri}>
                      <TableCell>{env.label}</TableCell>
                      <TableCell>{env.AwsAccountId}</TableCell>
                      <TableCell>{env.region}</TableCell>
                      <TableCell>
                        <StackStatus status={env.stack?.status} />
                      </TableCell>
                      <TableCell align="right">
                        <IconButton
                          onClick={() =>
                            navigate(
                              `/console/environments/${env.environmentUri}`
                            )
                          }
                        >
                          <ArrowRightIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow hover>
                    <TableCell>No environments linked</TableCell>
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
  );
};
OrganizationEnvironments.propTypes = {
  organization: PropTypes.object.isRequired
};
