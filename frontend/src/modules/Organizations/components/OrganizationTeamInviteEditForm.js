import React, { useCallback, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import {
  Box,
  Button,
  CardContent,
  CardHeader,
  CircularProgress,
  Dialog,
  Divider,
  FormControlLabel,
  FormGroup,
  Paper,
  Switch,
  Typography
} from '@mui/material';
import {
  listOrganizationGroupPermissions,
  updateOrganizationGroup
} from '../services';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { GroupAddOutlined } from '@mui/icons-material';

export const OrganizationTeamInviteEditForm = (props) => {
  const {
    organization,
    team,
    allPermissions,
    onClose,
    open,
    reloadTeams,
    enqueueSnackbar,
    ...other
  } = props;
  const [loading, setLoading] = useState(true);
  const dispatch = useDispatch();
  const client = useClient();
  const [selected_permissions, setSelectedPermissions] = useState([]);
  const [switchState, setSwitchState] = useState(false);
  const [changed, setChanged] = useState(false);

  const fetchGroupPermissions = useCallback(async () => {
    try {
      setLoading(true);
      const response = await client.query(
        listOrganizationGroupPermissions({
          organizationUri: organization.organizationUri,
          groupUri: team.groupUri
        })
      );
      if (!response.errors) {
        const group_permissions =
          response.data.listOrganizationGroupPermissions.map((p) => p.name);
        setSelectedPermissions(
          allPermissions.map((p) => ({
            name: p.name,
            description: p.description,
            selected: group_permissions.includes(p.name)
          }))
        );
        setSwitchState(
          allPermissions.reduce((acc, permission) => {
            acc[permission.name] = group_permissions.includes(permission.name);
            return acc;
          }, {})
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoading(false);
    }
  }, [client, dispatch, allPermissions, organization, team]);

  useEffect(() => {
    if (client) {
      fetchGroupPermissions().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch, setSelectedPermissions, fetchGroupPermissions]);

  async function submit() {
    try {
      setLoading(true);
      const response = await client.mutate(
        updateOrganizationGroup({
          groupUri: team.groupUri,
          organizationUri: organization.organizationUri,
          permissions: selected_permissions
            .filter((p) => p.selected)
            .map((p) => p.name)
        })
      );
      if (!response.errors) {
        enqueueSnackbar('Team permissions updated', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        if (reloadTeams) {
          reloadTeams();
        }
        if (onClose) {
          onClose();
        }
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (err) {
      console.error(err);
      dispatch({ type: SET_ERROR, error: err.message });
    } finally {
      setLoading(false);
    }
  }

  if (!organization) {
    return null;
  }

  if (loading) {
    return <CircularProgress size={10} />;
  }

  return (
    <Dialog maxWidth="lg" fullWidth onClose={onClose} open={open} {...other}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h4"
        >
          Team {team.groupUri}
        </Typography>
        <Typography align="center" color="textSecondary" variant="subtitle2">
          A Team is a group from your identity provider that you are a member
          of. All members of that group will inherit the permissions to view the
          organization.
        </Typography>
        <Box sx={{ p: 3 }}>
          <CardContent>
            <Paper>
              <CardHeader title="Organization Permissions" />
              <Divider />
              <CardContent sx={{ ml: 2 }}>
                {selected_permissions.length > 0 ? (
                  selected_permissions.map((perm) => (
                    <Box>
                      <FormGroup>
                        <FormControlLabel
                          color="primary"
                          control={
                            <Switch
                              checked={switchState[perm.name]}
                              color="primary"
                              edge="start"
                              name={perm.name}
                              value={perm.name}
                              onChange={(evt) => {
                                perm.selected = evt.target.checked;
                                const switchState_tmp = { ...switchState };
                                switchState_tmp[perm.name] = perm.selected;
                                setSwitchState(switchState_tmp);
                                setChanged(true);
                              }}
                            />
                          }
                          label={perm.description}
                          labelPlacement="end"
                          value={perm.name}
                        />
                      </FormGroup>
                    </Box>
                  ))
                ) : (
                  <Typography color="textPrimary" variant="subtitle2">
                    Failed to load permissions.
                  </Typography>
                )}
              </CardContent>
              <CardContent>
                <Button
                  disabled={!changed}
                  fullWidth
                  startIcon={<GroupAddOutlined fontSize="small" />}
                  color="primary"
                  variant="contained"
                  onClick={() => submit()}
                >
                  Update
                </Button>
              </CardContent>
            </Paper>
          </CardContent>
        </Box>
      </Box>
    </Dialog>
  );
};

OrganizationTeamInviteEditForm.propTypes = {
  organization: PropTypes.object.isRequired,
  team: PropTypes.object.isRequired,
  onClose: PropTypes.func,
  reloadTeams: PropTypes.func,
  open: PropTypes.bool.isRequired,
  allPermissions: PropTypes.any
};
