import React, { useCallback, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { useSnackbar } from 'notistack';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  Dialog,
  Divider,
  FormControlLabel,
  FormGroup,
  Paper,
  Switch,
  TextField,
  Typography
} from '@mui/material';
import Autocomplete from '@mui/lab/Autocomplete';
import { Formik } from 'formik';
import * as Yup from 'yup';
import { LoadingButton } from '@mui/lab';
import { GroupAddOutlined } from '@mui/icons-material';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import useClient from '../../hooks/useClient';
import inviteGroupToOrganization from '../../api/Organization/inviteGroup';
import listCognitoGroups from '../../api/Groups/listCognitoGroups';

const OrganizationTeamInviteForm = (props) => {
  const { organization, onClose, open, reloadTeams, ...other } = props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingGroups, setLoadingGroups] = useState(true);
  const [groupOptions, setGroupOptions] = useState([]);

  const filter = {
    type: "organization",
    uri: organization.organizationUri
  }

  const fetchGroups = useCallback(async () => {
    try {
      setLoadingGroups(true);
      const response = await client.query(listCognitoGroups({ filter }));
      if (!response.errors) {
        setGroupOptions(
          response.data.listCognitoGroups.map((g) => ({
            ...g,
            value: g.groupName,
            label: g.groupName
          }))
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoadingGroups(false);
    }
  }, [client, dispatch, organization.organizationUri]);

  const fetchItems = useCallback(async () => {
    try {
      setLoading(true);
      setPermissions([
        {
          name: 'LINK_ENVIRONMENTS',
          description: 'Link environments to this organization'
        },
        {
          name: 'INVITE_ENVIRONMENT_GROUP',
          description: 'Invite teams to this organization'
        }
      ]);
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    } finally {
      setLoading(false);
    }
  }, [dispatch]);

  useEffect(() => {
    if (client) {
      fetchGroups().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch, fetchItems, fetchGroups]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        inviteGroupToOrganization({
          groupUri: values.groupUri,
          organizationUri: organization.organizationUri
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Team invited to organization', {
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
      setStatus({ success: false });
      setErrors({ submit: err.message });
      setSubmitting(false);
      dispatch({ type: SET_ERROR, error: err.message });
    }
  }

  if (!organization) {
    return null;
  }

  if (loading || loadingGroups) {
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
          Invite a team to organization {organization.label}
        </Typography>
        <Typography align="center" color="textSecondary" variant="subtitle2">
          A Team is a group from your identity provider that you are a member
          of. All members of that group will be able to access your
          organization.
        </Typography>
        {loadingGroups ? (
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography color="textPrimary" variant="subtitle2">
                All your teams (IDP groups) are already invited to this
                organization.
              </Typography>
            </CardContent>
          </Card>
        ) : (
          <Box sx={{ p: 3 }}>
            <Formik
              initialValues={{
                groupUri: ''
              }}
              validationSchema={Yup.object().shape({
                groupUri: Yup.string()
                  .max(255)
                  .required('*Team name is required')
              })}
              onSubmit={async (
                values,
                { setErrors, setStatus, setSubmitting }
              ) => {
                await submit(values, setStatus, setSubmitting, setErrors);
              }}
            >
              {({
                errors,
                handleChange,
                handleSubmit,
                isSubmitting,
                setFieldValue,
                touched,
                values
              }) => (
                <form onSubmit={handleSubmit}>
                  <CardContent>
                    <Autocomplete
                      id="groupUri"
                      freeSolo
                      options={groupOptions.map((option) => option.value)}
                      onChange={(event, value) => {
                        setFieldValue('groupUri', value);
                      }}
                      renderInput={(params) => (
                        <TextField
                          {...params}
                          label="Team"
                          margin="normal"
                          error={Boolean(touched.groupUri && errors.groupUri)}
                          helperText={touched.groupUri && errors.groupUri}
                          onChange={handleChange}
                          value={values.groupUri}
                          variant="outlined"
                        />
                      )}
                    />
                  </CardContent>
                  <CardContent>
                    <Paper>
                      <CardHeader title="Organization Permissions" />
                      <Divider />
                      <CardContent sx={{ ml: 2 }}>
                        {permissions.length > 0 ? (
                          permissions.map((perm) => (
                            <Box>
                              <FormGroup>
                                <FormControlLabel
                                  color="primary"
                                  control={
                                    <Switch
                                      disabled
                                      defaultChecked
                                      color="primary"
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
                      </CardContent>
                    </Paper>
                  </CardContent>
                  <Box>
                    <CardContent>
                      <LoadingButton
                        fullWidth
                        startIcon={<GroupAddOutlined fontSize="small" />}
                        color="primary"
                        disabled={isSubmitting}
                        type="submit"
                        variant="contained"
                      >
                        Invite Team
                      </LoadingButton>
                    </CardContent>
                  </Box>
                </form>
              )}
            </Formik>
          </Box>
        )}
      </Box>
    </Dialog>
  );
};

OrganizationTeamInviteForm.propTypes = {
  organization: PropTypes.object.isRequired,
  onClose: PropTypes.func,
  reloadTeams: PropTypes.func,
  open: PropTypes.bool.isRequired
};

export default OrganizationTeamInviteForm;
