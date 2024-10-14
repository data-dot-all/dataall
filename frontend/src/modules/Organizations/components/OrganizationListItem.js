import {
  Box,
  Button,
  Card,
  Divider,
  Grid,
  Link,
  Tooltip,
  Typography
} from '@mui/material';
import PropTypes from 'prop-types';
import React from 'react';
import * as BiIcon from 'react-icons/bi';
import * as FaIcons from 'react-icons/fa';
import { FaUserPlus } from 'react-icons/fa';
import { useNavigate } from 'react-router';
import { Link as RouterLink } from 'react-router-dom';
import { IconAvatar, Label, useCardStyle } from 'design';

export const OrganizationListItem = (props) => {
  const { organization } = props;
  const classes = useCardStyle();
  const navigate = useNavigate();
  return (
    <Grid item key={organization.orgnanizationUri} md={3} xs={12} {...props}>
      <Card key={organization.orgnanizationUri} className={classes.card} raised>
        <Box sx={{ p: 2 }}>
          <Grid container>
            <Grid item md={11} xs={11}>
              <Box
                sx={{
                  display: 'flex'
                }}
              >
                <IconAvatar icon={<BiIcon.BiBuildings size={15} />} />
                <Box sx={{ ml: 2 }}>
                  <Link
                    underline="hover"
                    component="button"
                    color="textPrimary"
                    variant="h6"
                    onClick={() => {
                      navigate(
                        `/console/organizations/${organization.organizationUri}`
                      );
                    }}
                    sx={{
                      width: '99%',
                      whiteSpace: 'nowrap',
                      alignItems: 'left',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      WebkitBoxOrient: 'vertical',
                      WebkitLineClamp: 2
                    }}
                  >
                    <Tooltip title={organization.label}>
                      <span>{organization.label}</span>
                    </Tooltip>
                  </Link>
                  <Typography color="textSecondary" variant="body2">
                    by{' '}
                    <Link
                      underline="hover"
                      color="textPrimary"
                      variant="subtitle2"
                    >
                      {organization.owner}
                    </Link>
                  </Typography>
                </Box>
              </Box>
            </Grid>
          </Grid>
        </Box>
        <Box
          sx={{
            pb: 2,
            px: 3
          }}
        >
          <Typography
            color="textSecondary"
            variant="body2"
            sx={{
              width: '200px',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              WebkitBoxOrient: 'vertical',
              WebkitLineClamp: 2
            }}
          >
            <Tooltip
              title={organization.description || 'No description provided'}
            >
              <span>
                {organization.description || 'No description provided'}
              </span>
            </Tooltip>
          </Typography>
        </Box>
        <Box
          sx={{
            px: 3,
            py: 0.5
          }}
        >
          <Grid container>
            <Grid item md={5} xs={6}>
              <Typography color="textSecondary" variant="body2">
                <FaIcons.FaUserShield /> Role
              </Typography>
            </Grid>
            <Grid item md={7} xs={6}>
              <Label
                color={
                  organization.userRoleInOrganization === 'Owner'
                    ? 'primary'
                    : 'info'
                }
              >
                {organization.userRoleInOrganization || '-'}
              </Label>
            </Grid>
          </Grid>
        </Box>
        <Box
          sx={{
            px: 3,
            py: 0.5
          }}
        >
          <Grid container>
            <Grid item md={5} xs={12}>
              <Typography color="textSecondary" variant="body2">
                <FaIcons.FaUsersCog /> Team
              </Typography>
            </Grid>
            <Grid item md={7} xs={6}>
              <Typography
                color="textPrimary"
                variant="body2"
                sx={{
                  width: '200px',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  WebkitBoxOrient: 'vertical',
                  WebkitLineClamp: 2
                }}
              >
                <Tooltip title={organization.SamlGroupName || '-'}>
                  <span>{organization.SamlGroupName || '-'}</span>
                </Tooltip>
              </Typography>
            </Grid>
          </Grid>
        </Box>
        <Box
          sx={{
            px: 3,
            py: 0.5
          }}
        >
          <Grid container>
            <Grid item md={5} xs={6}>
              <Typography color="textSecondary" variant="body2">
                <FaIcons.FaAws /> Environments
              </Typography>
            </Grid>
            <Grid item md={7} xs={6}>
              <Typography color="textPrimary" variant="body2">
                {organization.stats.environments}
              </Typography>
            </Grid>
          </Grid>
        </Box>
        <Box
          sx={{
            px: 3,
            py: 0.5
          }}
        >
          <Grid container>
            <Grid item md={5} xs={6}>
              <Typography color="textSecondary" variant="body2">
                <FaUserPlus /> Teams
              </Typography>
            </Grid>
            <Grid item md={7} xs={6}>
              <Typography color="textPrimary" variant="body2">
                {organization.stats.groups}
              </Typography>
            </Grid>
          </Grid>
        </Box>
        <Box
          sx={{
            px: 3,
            py: 1
          }}
        >
          <Grid
            alignItems="center"
            container
            key={organization.organizationUri}
            justifyContent="space-between"
            spacing={3}
          />
        </Box>
        <Divider />
        <Box
          sx={{
            alignItems: 'center',
            display: 'flex',
            pl: 1,
            pr: 3,
            py: 0.5
          }}
        >
          <Box
            sx={{
              alignItems: 'center',
              display: 'flex'
            }}
          >
            <Button
              color="primary"
              component={RouterLink}
              to={`/console/organizations/${organization.organizationUri}`}
            >
              Learn More
            </Button>
          </Box>
        </Box>
      </Card>
    </Grid>
  );
};
OrganizationListItem.propTypes = {
  organization: PropTypes.object.isRequired
};
