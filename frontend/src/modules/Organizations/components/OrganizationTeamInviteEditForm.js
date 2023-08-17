import React, { useState } from 'react';
import PropTypes from 'prop-types';
import {
  Box,
  CardContent,
  CardHeader,
  Dialog,
  Divider,
  FormControlLabel,
  FormGroup,
  Paper,
  Switch,
  TextField,
  Typography
} from '@mui/material';

export const OrganizationTeamInviteEditForm = (props) => {
  const { organization, team, onClose, open, reloadTeams, ...other } = props;
  const [permissions] = useState([
    {
      name: 'LINK_ENVIRONMENTS',
      description: 'Link environments to this organization'
    },
    {
      name: 'INVITE_ENVIRONMENT_GROUP',
      description: 'Invite teams to this organization'
    }
  ]);

  if (!organization) {
    return null;
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
          of. All members of that group will be able to access your environment.
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
  open: PropTypes.bool.isRequired
};
