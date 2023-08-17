import { GroupAddOutlined } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import {
  Box,
  CardContent,
  CardHeader,
  CircularProgress,
  Dialog,
  Divider,
  FormControlLabel,
  FormGroup,
  FormHelperText,
  Paper,
  Switch,
  TextField,
  Typography
} from '@mui/material';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import {
  listTenantPermissions,
  updateTenantGroupPermissions
} from '../services';

export const TeamPermissionsEditForm = (props) => {
  const { team, onClose, open, reloadTeams, ...other } = props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const [permissions, setPermissions] = useState(
    team.tenantPermissions.map((perm) => perm.name)
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [permissionsError, setPermissionsError] = useState(null);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchItems = useCallback(async () => {
    try {
      setLoading(true);
      const response = await client.query(listTenantPermissions({}));
      if (!response.errors) {
        setItems(response.data.listTenantPermissions);
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoading(false);
    }
  }, [client, dispatch]);

  useEffect(() => {
    if (client) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch, fetchItems]);

  /**
   * @description Handle Submit action.
   * @returns {Promise<void>}
   */
  const submit = async () => {
    setIsSubmitting(true);
    try {
      if (!permissions || permissions.length < 1) {
        setPermissionsError('* At least one permission is required');
      } else {
        const response = await client.mutate(
          updateTenantGroupPermissions({
            groupUri: team.groupUri,
            permissions
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
      }
    } catch (err) {
      console.error(err);
      dispatch({ type: SET_ERROR, error: err.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return <CircularProgress size={15} />;
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
          A Team is a group from your identity provider that has access to
          data.all. Administrators can manage permissions for each team.
        </Typography>
        <Box sx={{ p: 3 }}>
          <CardContent>
            <TextField
              disabled
              fullWidth
              label="Team"
              name="team"
              value={team.groupUri}
              variant="outlined"
            />
          </CardContent>
          <CardContent>
            <Paper>
              <CardHeader title="Tenant Permissions" />
              <Divider />
              <CardContent sx={{ ml: 2 }}>
                {items.length > 0 ? (
                  items.map((perm) => (
                    <Box>
                      <FormGroup>
                        <FormControlLabel
                          color="primary"
                          control={
                            <Switch
                              defaultChecked={
                                team.tenantPermissions.filter(
                                  (tenantPerm) => tenantPerm.name === perm.name
                                ).length === 1
                              }
                              color="primary"
                              onChange={(event) => {
                                const newPerms = permissions;
                                if (event.target.checked) {
                                  newPerms.push(event.target.value);
                                } else {
                                  const index = newPerms.indexOf(
                                    event.target.value
                                  );
                                  if (index > -1) {
                                    newPerms.splice(index, 1);
                                  }
                                }
                                setPermissions(newPerms);
                              }}
                              edge="start"
                              name={perm.name}
                              value={perm.name}
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
                {permissionsError && (
                  <Box sx={{ mt: 2 }}>
                    <FormHelperText error>{permissionsError}</FormHelperText>
                  </Box>
                )}
              </CardContent>
            </Paper>
          </CardContent>
          <Box>
            <CardContent>
              <LoadingButton
                fullWidth
                startIcon={<GroupAddOutlined fontSize="small" />}
                color="primary"
                loading={isSubmitting}
                type="submit"
                onClick={() => submit()}
                variant="contained"
              >
                Save
              </LoadingButton>
            </CardContent>
          </Box>
        </Box>
      </Box>
    </Dialog>
  );
};

TeamPermissionsEditForm.propTypes = {
  team: PropTypes.object.isRequired,
  onClose: PropTypes.func,
  reloadTeams: PropTypes.func,
  open: PropTypes.bool.isRequired
};
