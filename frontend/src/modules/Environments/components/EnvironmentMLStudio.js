import { LoadingButton } from '@mui/lab';
import {
  Box,
  Card,
  CardHeader,
  Chip,
  Divider,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import { FaNetworkWired } from 'react-icons/fa';
import { Defaults, Pager, PlusIcon, RefreshTableMenu, Scrollbar } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import {
  deleteMLStudioDomain,
  listEnvironmentMLStudioDomains
} from '../services';
import { MLStudioDomainCreateModal } from './MLStudioDomainCreateModal';

function DomainRow({ domain }) {
  return (
    <TableRow hover>
      <TableCell>{domain.label}</TableCell>
      <TableCell>{domain.sagemakerStudioDomainName}</TableCell>
      <TableCell>{domain.vpcId}</TableCell>
      <TableCell>
        {domain.subnetIds && (
          <Box
            sx={{
              pb: 2,
              px: 3
            }}
          >
            {domain.subnetIds.map((subnet) => (
              <Chip
                size="small"
                sx={{ mr: 0.5 }}
                key={subnet}
                label={subnet}
                variant="outlined"
              />
            ))}
          </Box>
        )}
      </TableCell>
    </TableRow>
  );
}

DomainRow.propTypes = {
  domain: PropTypes.any
};
export const EnvironmentMLStudio = ({ environment }) => {
  const client = useClient();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const [loading, setLoading] = useState(true);
  const [isStudioDomainCreateOpen, setStudioDomainCreateOpen] = useState(false);
  const handleStudioDomainCreateModalOpen = () => {
    setStudioDomainCreateOpen(true);
  };

  const handleStudioDomainCreateModalClose = () => {
    setStudioDomainCreateOpen(false);
  };

  const fetchItems = useCallback(async () => {
    try {
      const response = await client.query(
        listEnvironmentMLStudioDomains({
          environmentUri: environment.environmentUri,
          filter
        })
      );
      if (!response.errors) {
        setItems({ ...response.data.listEnvironmentMLStudioDomains });
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoading(false);
    }
  }, [client, dispatch, filter, environment.environmentUri]);

  const deleteEnvironmentMLStudioDomain = async (sagemakerStudioUri) => {
    const response = await client.mutate(
      deleteMLStudioDomain({ sagemakerStudioUri: sagemakerStudioUri })
    );
    if (!response.errors) {
      enqueueSnackbar('ML Studio Domain deleted', {
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
  };

  useEffect(() => {
    if (client) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, filter.page, fetchItems, dispatch]);

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
              <FaNetworkWired style={{ marginRight: '10px' }} /> ML Studio
              Domains
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
          <Grid item md={2} sm={6} xs={12}>
            {items.nodes.length === 0 ? (
              <LoadingButton
                color="primary"
                onClick={handleStudioDomainCreateModalOpen}
                startIcon={<PlusIcon fontSize="small" />}
                sx={{ m: 1 }}
                variant="outlined"
              >
                Add ML Studio Domain
              </LoadingButton>
            ) : (
              <LoadingButton
                color="primary"
                onClick={deleteEnvironmentMLStudioDomain}
                startIcon={<PlusIcon fontSize="small" />}
                sx={{ m: 1 }}
                variant="outlined"
              >
                Delete ML Studio Domain
              </LoadingButton>
            )}
          </Grid>
        </Box>
        <Scrollbar>
          <Box sx={{ minWidth: 600 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Domain Name</TableCell>
                  <TableCell>VPC</TableCell>
                  <TableCell>Subnets</TableCell>
                </TableRow>
              </TableHead>
              {loading ? (
                <CircularProgress sx={{ mt: 1 }} />
              ) : (
                <TableBody>
                  {items.nodes.length > 0 ? (
                    items.nodes.map((domain) => (
                      <DomainRow
                        domain={domain}
                        environment={environment}
                        fetchItems={fetchItems}
                      />
                    ))
                  ) : (
                    <TableRow hover>
                      <TableCell>No SageMaker Studio Domain Found</TableCell>
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
      {isStudioDomainCreateOpen && (
        <MLStudioDomainCreateModal
          environment={environment}
          onApply={handleStudioDomainCreateModalClose}
          onClose={handleStudioDomainCreateModalClose}
          reloadStudioDomains={fetchItems}
          open={isStudioDomainCreateOpen}
        />
      )}
    </Box>
  );
};

EnvironmentMLStudio.propTypes = {
  environment: PropTypes.object.isRequired
};
