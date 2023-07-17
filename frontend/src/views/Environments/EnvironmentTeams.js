import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardHeader,
  Chip,
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
import {
  CopyAllOutlined,
  DeleteOutlined,
  GroupAddOutlined,
  SupervisedUserCircleRounded
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import * as FaIcons from 'react-icons/fa';
import { LoadingButton } from '@mui/lab';
import { useTheme } from '@mui/styles';
import { HiUserRemove } from 'react-icons/hi';
import { VscChecklist } from 'react-icons/vsc';
import useClient from '../../hooks/useClient';
import * as Defaults from '../../components/defaults';
import SearchIcon from '../../icons/Search';
import Scrollbar from '../../components/Scrollbar';
import RefreshTableMenu from '../../components/RefreshTableMenu';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import Pager from '../../components/Pager';
import Label from '../../components/Label';
import EnvironmentTeamInviteForm from './EnvironmentTeamInviteForm';
import EnvironmentRoleAddForm from './EnvironmentRoleAddForm';
import removeGroupFromEnvironment from '../../api/Environment/removeGroup';
import removeConsumptionRoleFromEnvironment from '../../api/Environment/removeConsumptionRole';
import getEnvironmentAssumeRoleUrl from '../../api/Environment/getEnvironmentAssumeRoleUrl';
import EnvironmentTeamInviteEditForm from './EnvironmentTeamInviteEditForm';
import generateEnvironmentAccessToken from '../../api/Environment/generateEnvironmentAccessToken';
import listAllEnvironmentGroups from '../../api/Environment/listAllEnvironmentGroups';
import listAllEnvironmentConsumptionRoles from '../../api/Environment/listAllEnvironmentConsumptionRoles';

function TeamRow({ team, environment, fetchItems }) {
  const client = useClient();
  const dispatch = useDispatch();
  const theme = useTheme();
  const { enqueueSnackbar } = useSnackbar();
  const [accessingConsole, setAccessingConsole] = useState(false);
  const [loadingCreds, setLoadingCreds] = useState(false);
  const [isTeamEditModalOpen, setIsTeamEditModalOpen] = useState(false);
  const handleTeamEditModalClose = () => {
    setIsTeamEditModalOpen(false);
  };

  const handleTeamEditModalOpen = () => {
    setIsTeamEditModalOpen(true);
  };

  const removeGroup = async (groupUri) => {
    try {
      const response = await client.mutate(
        removeGroupFromEnvironment({
          environmentUri: environment.environmentUri,
          groupUri
        })
      );
      if (!response.errors) {
        enqueueSnackbar('Team removed from environment', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        if (fetchItems) {
          fetchItems();
        }
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
  };

  const getConsoleLink = async (groupUri) => {
    setAccessingConsole(true);
    const response = await client.query(
      getEnvironmentAssumeRoleUrl({
        environmentUri: environment.environmentUri,
        groupUri
      })
    );
    if (!response.errors) {
      window.open(response.data.getEnvironmentAssumeRoleUrl, '_blank');
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setAccessingConsole(false);
  };

  const generateCredentials = async (groupUri) => {
    setLoadingCreds(true);
    const response = await client.query(
      generateEnvironmentAccessToken({
        environmentUri: environment.environmentUri,
        groupUri
      })
    );
    if (!response.errors) {
      await navigator.clipboard.writeText(
        response.data.generateEnvironmentAccessToken
      );
      enqueueSnackbar('Credentials copied to clipboard', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoadingCreds(false);
  };
  return (
    <TableRow hover>
      <TableCell>
        {team.groupUri}{' '}
        {team.groupUri === environment.SamlGroupName && (
          <Label color="primary">Admins</Label>
        )}
      </TableCell>
      <TableCell>{team.environmentIAMRoleArn}</TableCell>
      <TableCell>{team.environmentAthenaWorkGroup}</TableCell>
      <TableCell>
        {team.groupUri !== environment.SamlGroupName ? (
          <LoadingButton onClick={() => handleTeamEditModalOpen(team)}>
            <VscChecklist
              size={20}
              color={
                theme.palette.mode === 'dark'
                  ? theme.palette.primary.contrastText
                  : theme.palette.primary.main
              }
            />
          </LoadingButton>
        ) : (
          <Chip
            size="small"
            sx={{ ml: 1.5 }}
            key="ALL"
            label="ALL"
            variant="outlined"
          />
        )}
        {isTeamEditModalOpen && (
          <EnvironmentTeamInviteEditForm
            environment={environment}
            team={team}
            open
            reloadTeams={fetchItems}
            onClose={handleTeamEditModalClose}
          />
        )}
      </TableCell>
      <TableCell>
        <Box>
          <LoadingButton
            loading={accessingConsole}
            onClick={() => getConsoleLink(team.groupUri)}
          >
            <FaIcons.FaAws
              size={25}
              color={
                theme.palette.mode === 'dark'
                  ? theme.palette.primary.contrastText
                  : theme.palette.primary.main
              }
            />
          </LoadingButton>
          <LoadingButton
            loading={loadingCreds}
            onClick={() => generateCredentials(team.groupUri)}
          >
            <CopyAllOutlined
              sx={{
                color:
                  theme.palette.mode === 'dark'
                    ? theme.palette.primary.contrastText
                    : theme.palette.primary.main
              }}
            />
          </LoadingButton>
          {team.groupUri !== environment.SamlGroupName && (
            <LoadingButton onClick={() => removeGroup(team.groupUri)}>
              <HiUserRemove
                size={25}
                color={
                  theme.palette.mode === 'dark'
                    ? theme.palette.primary.contrastText
                    : theme.palette.primary.main
                }
              />
            </LoadingButton>
          )}
        </Box>
      </TableCell>
    </TableRow>
  );
}

TeamRow.propTypes = {
  team: PropTypes.any,
  environment: PropTypes.any,
  fetchItems: PropTypes.any
};

const EnvironmentTeams = ({ environment }) => {
  const client = useClient();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const [items, setItems] = useState(Defaults.PagedResponseDefault);
  const [roles, setRoles] = useState(Defaults.PagedResponseDefault);
  const [filter, setFilter] = useState(Defaults.DefaultFilter);
  const [filterRoles, setFilterRoles] = useState(Defaults.DefaultFilter);
  const [loading, setLoading] = useState(true);
  const [inputValue, setInputValue] = useState('');
  const [inputValueRoles, setInputValueRoles] = useState('');
  const [isTeamInviteModalOpen, setIsTeamInviteModalOpen] = useState(false);
  const [isAddRoleModalOpen, setIsAddRoleModalOpen] = useState(false);
  const handleTeamInviteModalOpen = () => {
    setIsTeamInviteModalOpen(true);
  };
  const handleTeamInviteModalClose = () => {
    setIsTeamInviteModalOpen(false);
  };
  const handleAddRoleModalOpen = () => {
    setIsAddRoleModalOpen(true);
  };
  const handleAddRoleModalClose = () => {
    setIsAddRoleModalOpen(false);
  };

  const fetchItems = useCallback(async () => {
    try {
      const response = await client.query(
        listAllEnvironmentGroups({
          environmentUri: environment.environmentUri,
          filter
        })
      );
      if (!response.errors) {
        setItems({ ...response.data.listAllEnvironmentGroups });
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoading(false);
    }
  }, [client, dispatch, environment, filter]);

  const fetchRoles= useCallback(async () => {
    try {
      const response = await client.query(
        listAllEnvironmentConsumptionRoles({
          environmentUri: environment.environmentUri,
          filterRoles
        })
      );
      if (!response.errors) {
        setRoles({ ...response.data.listAllEnvironmentConsumptionRoles });
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoading(false);
    }
  }, [client, dispatch, environment, filterRoles]);

  const removeConsumptionRole = async (consumptionGroupUri) => {
    console.log(consumptionGroupUri)
    try {
      const response = await client.mutate(
        removeConsumptionRoleFromEnvironment({
          environmentUri: environment.environmentUri,
          consumptionRoleUri: consumptionGroupUri
        })
      );
      if (!response.errors) {
        enqueueSnackbar('Consumption Role removed from environment', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        fetchRoles();
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
  };


  useEffect(() => {
    if (client) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      fetchRoles().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, filter.page, filterRoles.page, fetchItems, fetchRoles, dispatch]);

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

  const handleInputChangeRoles = (event) => {
    setInputValueRoles(event.target.value);
    setFilterRoles({ ...filterRoles, term: event.target.value });
  };

  const handleInputKeyupRoles = (event) => {
    if (event.code === 'Enter') {
      fetchRoles().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  };

  const handlePageChangeRoles = async (event, value) => {
    if (value <= roles.pages && value !== roles.page) {
      await setFilterRoles({ ...filterRoles, page: value });
    }
  };

  return (
    <Box>
      <Box>
        <Card>
        <CardHeader
          action={<RefreshTableMenu refresh={fetchItems} />}
          title={
            <Box>
              <SupervisedUserCircleRounded style={{ marginRight: '10px' }} />{' '}
              Environment Teams
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
          <Grid item md={2} sm={6} xs={12}>
            <Button
              color="primary"
              startIcon={<GroupAddOutlined fontSize="small" />}
              sx={{ m: 1 }}
              onClick={handleTeamInviteModalOpen}
              variant="contained"
            >
              Invite
            </Button>
            {isTeamInviteModalOpen && (
              <EnvironmentTeamInviteForm
                environment={environment}
                open
                reloadTeams={fetchItems}
                onClose={handleTeamInviteModalClose}
              />
            )}
          </Grid>
        </Box>
        <Scrollbar>
          <Box sx={{ minWidth: 600 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>IAM Role</TableCell>
                  <TableCell>Athena WorkGroup</TableCell>
                  <TableCell>Permissions</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              {loading ? (
                <CircularProgress sx={{ mt: 1 }} />
              ) : (
                <TableBody>
                  {items.nodes.length > 0 ? (
                    items.nodes.map((team) => (
                      <TeamRow
                        team={team}
                        environment={environment}
                        fetchItems={fetchItems}
                      />
                    ))
                  ) : (
                    <TableRow hover>
                      <TableCell>No Team invited</TableCell>
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
      <Box sx={{ mt: 3 }}>
        <Card>
        <CardHeader
          action={<RefreshTableMenu refresh={fetchRoles} />}
          title={
            <Box>
              <SupervisedUserCircleRounded style={{ marginRight: '10px' }} />{' '}
              Environment Consumption IAM roles
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
                onChange={handleInputChangeRoles}
                onKeyUp={handleInputKeyupRoles}
                placeholder="Search"
                value={inputValueRoles}
                variant="outlined"
              />
            </Box>
          </Grid>
          <Grid item md={2} sm={6} xs={12}>
            <Button
              color="primary"
              startIcon={<GroupAddOutlined fontSize="small" />}
              sx={{ m: 1 }}
              onClick={handleAddRoleModalOpen}
              variant="contained"
            >
              Add Consumption Role
            </Button>
            {isAddRoleModalOpen && (
              <EnvironmentRoleAddForm
                environment={environment}
                open
                reloadRoles={fetchRoles}
                onClose={handleAddRoleModalClose}
              />
            )}
          </Grid>
        </Box>
        <Scrollbar>
          <Box sx={{ minWidth: 600 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>IAM Role</TableCell>
                  <TableCell>Role Owner</TableCell>
                  <TableCell>Action</TableCell>
                </TableRow>
              </TableHead>
              {loading ? (
                <CircularProgress sx={{ mt: 1 }} />
              ) : (
                <TableBody>
                  {roles.nodes.length > 0 ? (
                    roles.nodes.map((role) => (
                      <TableRow hover key={role.consumptionRoleUri}>
                        <TableCell>{role.consumptionRoleName}</TableCell>
                        <TableCell>{role.IAMRoleArn}</TableCell>
                        <TableCell>{role.groupUri}</TableCell>
                        <TableCell>
                          <IconButton onClick={() => removeConsumptionRole(role.consumptionRoleUri)}>
                            <DeleteOutlined fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow hover>
                      <TableCell>No Consumption IAM Role added</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              )}
            </Table>
            {!loading && roles.nodes.length > 0 && (
              <Pager
                mgTop={2}
                mgBottom={2}
                items={roles}
                onChange={handlePageChangeRoles}
              />
            )}
          </Box>
        </Scrollbar>
      </Card>
      </Box>
    </Box>
  );
};

EnvironmentTeams.propTypes = {
  environment: PropTypes.object.isRequired
};

export default EnvironmentTeams;
