import { useClient } from '../../../services';
import { SET_ERROR, useDispatch } from '../../../globalErrors';
import { useTheme } from '@mui/styles';
import { useSnackbar } from 'notistack';
import React, { useCallback, useEffect, useState } from 'react';
import { removeGroupFromOrganization } from '../services';
import {
  Box,
  Button,
  Card,
  CardHeader,
  Chip,
  Divider,
  Grid,
  InputAdornment,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField
} from '@mui/material';
import {
  Defaults,
  DeleteObjectWithFrictionModal,
  Label,
  Pager,
  RefreshTableMenu,
  Scrollbar,
  SearchIcon
} from '../../../design';
import { LoadingButton } from '@mui/lab';
import { VscChecklist } from 'react-icons/vsc';
import { OrganizationTeamInviteEditForm } from './OrganizationTeamInviteEditForm';
import { HiUserRemove } from 'react-icons/hi';
import PropTypes from 'prop-types';
import * as BsIcons from 'react-icons/bs';
import { GroupAddOutlined } from '@mui/icons-material';
import { OrganizationTeamInviteForm } from './OrganizationTeamInviteForm';
import CircularProgress from '@mui/material/CircularProgress';

function TeamRow({
  team,
  organization,
  fetchItems,
  showActions,
  showPermissions
}) {
  const client = useClient();
  const dispatch = useDispatch();
  const theme = useTheme();
  const { enqueueSnackbar } = useSnackbar();
  const [isPermissionModalOpen, setIsPermissionsModalOpen] = useState(false);
  const [isDeleteGroupModalOpen, setIsDeleteGroupModalOpenId] = useState(false);

  const handleDeleteGroupModalClosed = () => {
    setIsDeleteGroupModalOpenId(false);
  };

  const handleDeleteGroupModalOpen = () => {
    setIsDeleteGroupModalOpenId(true);
  };

  const handlePermissionsModalClose = () => {
    setIsPermissionsModalOpen(false);
  };

  const handlePermissionsModalOpen = () => {
    setIsPermissionsModalOpen(true);
  };
  const removeGroup = async (groupUri) => {
    try {
      const response = await client.mutate(
        removeGroupFromOrganization({
          organizationUri: organization.organizationUri,
          groupUri
        })
      );
      if (!response.errors) {
        enqueueSnackbar('Team removed from organization', {
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

  return (
    <TableRow hover sx={{ height: '70px !important' }}>
      <TableCell>
        {team.groupUri}{' '}
        {team.groupUri === organization.SamlGroupName && (
          <Label color="primary">Admins</Label>
        )}
      </TableCell>
      {showPermissions && (
        <TableCell>
          {team.groupUri !== organization.SamlGroupName ? (
            <LoadingButton onClick={() => handlePermissionsModalOpen(team)}>
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
          {isPermissionModalOpen && (
            <OrganizationTeamInviteEditForm
              organization={organization}
              team={team}
              open
              reloadTeams={fetchItems}
              onClose={handlePermissionsModalClose}
            />
          )}
        </TableCell>
      )}

      {showActions && (
        <TableCell>
          <Box>
            {team.groupUri !== organization.SamlGroupName &&
              organization.canRemoveGroup && (
                <LoadingButton onClick={() => handleDeleteGroupModalOpen()}>
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
            {team.groupUri !== organization.SamlGroupName && (
              <DeleteObjectWithFrictionModal
                objectName={team.groupUri}
                onApply={() => handleDeleteGroupModalClosed()}
                onClose={() => handleDeleteGroupModalClosed()}
                open={isDeleteGroupModalOpen}
                isAWSResource={false}
                deleteFunction={() => removeGroup(team.groupUri)}
              />
            )}
          </Box>
        </TableCell>
      )}
    </TableRow>
  );
}

TeamRow.propTypes = {
  team: PropTypes.any,
  organization: PropTypes.any,
  fetchItems: PropTypes.any
};

export function TeamsTableCard({
  organization,
  teamsName,
  showActions,
  showPermissions,
  showInvite,
  queryFunction,
  resultName
}) {
  const client = useClient();
  const dispatch = useDispatch();
  const [items, setItems] = useState(Defaults.pagedResponse);
  const [filter, setFilter] = useState(Defaults.filter);
  const [loading, setLoading] = useState(true);
  const [inputValue, setInputValue] = useState('');
  const [isTeamInviteModalOpen, setIsTeamInviteModalOpen] = useState(false);
  const handleTeamInviteModalOpen = () => {
    setIsTeamInviteModalOpen(true);
  };
  const handleTeamInviteModalClose = () => {
    setIsTeamInviteModalOpen(false);
  };

  const fetchItems = useCallback(async () => {
    setLoading(true);
    try {
      const response = await client.query(
        queryFunction({
          organizationUri: organization.organizationUri,
          filter
        })
      );
      if (!response.errors) {
        setItems({ ...response.data[resultName] });
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoading(false);
    }
  }, [client, dispatch, filter, organization.organizationUri]);

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
    <Card sx={{ height: '100%' }}>
      <CardHeader
        action={<RefreshTableMenu refresh={fetchItems} />}
        title={
          <Box>
            <BsIcons.BsPeople style={{ marginRight: '10px' }} /> {teamsName}
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
          {organization.canInvite && showInvite && (
            <Button
              color="primary"
              startIcon={<GroupAddOutlined fontSize="small" />}
              sx={{ m: 1 }}
              onClick={handleTeamInviteModalOpen}
              variant="contained"
            >
              Invite
            </Button>
          )}

          {isTeamInviteModalOpen && (
            <OrganizationTeamInviteForm
              organization={organization}
              open
              reloadTeams={fetchItems}
              onClose={handleTeamInviteModalClose}
            />
          )}
        </Grid>
      </Box>
      <Scrollbar>
        <Box>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                {showPermissions && <TableCell>Permissions</TableCell>}
                {showActions && <TableCell>Actions</TableCell>}
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
                      organization={organization}
                      fetchItems={fetchItems}
                      showActions={showActions}
                      showPermissions={showPermissions}
                    />
                  ))
                ) : (
                  <TableRow hover>
                    <TableCell sx={{ height: '70px' }}>
                      No {teamsName.toLowerCase()} found
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
  );
}

TeamsTableCard.propTypes = {
  teams: PropTypes.any,
  organization: PropTypes.any,
  fetchItems: PropTypes.any
};