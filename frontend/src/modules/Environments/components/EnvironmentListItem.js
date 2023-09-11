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
import * as BsIcons from 'react-icons/bs';
import * as FaIcons from 'react-icons/fa';
import * as FiIcons from 'react-icons/fi';
import { useNavigate } from 'react-router';
import { Link as RouterLink } from 'react-router-dom';
import { IconAvatar, Label, StackStatus, useCardStyle } from 'design';

export const EnvironmentListItem = (props) => {
  const { environment } = props;
  const classes = useCardStyle();
  const navigate = useNavigate();
  return (
    <Grid item key={environment.environmentUri} md={3} xs={12} {...props}>
      <Card key={environment.environmentUri} className={classes.card} raised>
        <Box sx={{ p: 2 }}>
          <Grid container>
            <Grid item md={11} xs={11}>
              <Box
                sx={{
                  alignItems: 'center',
                  display: 'flex'
                }}
              >
                <IconAvatar icon={<BsIcons.BsCloudFill size={15} />} />
                <Box sx={{ ml: 2 }}>
                  <Link
                    underline="hover"
                    component="button"
                    color="textPrimary"
                    variant="h6"
                    onClick={() => {
                      navigate(
                        `/console/environments/${environment.environmentUri}`
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
                    <Tooltip title={environment.label}>
                      <span>{environment.label}</span>
                    </Tooltip>
                  </Link>
                  <Typography color="textSecondary" variant="body2">
                    by{' '}
                    <Link
                      underline="hover"
                      color="textPrimary"
                      variant="subtitle2"
                    >
                      {environment.owner}
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
              title={environment.description || 'No description provided'}
            >
              <span>
                {environment.description || 'No description provided'}
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
            <Grid item md={4} xs={12}>
              <Typography color="textSecondary" variant="body2">
                <FaIcons.FaUserShield /> Role
              </Typography>
            </Grid>
            <Grid item md={8} xs={12}>
              <Label
                color={
                  environment.userRoleInEnvironment === 'Owner'
                    ? 'primary'
                    : 'info'
                }
              >
                {environment.userRoleInEnvironment || '-'}
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
            <Grid item md={4} xs={12}>
              <Typography color="textSecondary" variant="body2">
                <FaIcons.FaUsersCog /> Team
              </Typography>
            </Grid>
            <Grid item md={8} xs={12}>
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
                <Tooltip title={environment.SamlGroupName || '-'}>
                  <span>{environment.SamlGroupName || '-'}</span>
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
            <Grid item md={4} xs={12}>
              <Typography color="textSecondary" variant="body2">
                <FaIcons.FaAws /> Account
              </Typography>
            </Grid>
            <Grid item md={8} xs={6}>
              <Typography color="textPrimary" variant="body2">
                {environment.AwsAccountId}
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
            <Grid item md={4} xs={12}>
              <Typography color="textSecondary" variant="body2">
                <FaIcons.FaGlobe /> Region
              </Typography>
            </Grid>
            <Grid item md={8} xs={12}>
              <Typography color="textPrimary" variant="body2">
                {environment.region}
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
            <Grid item md={4} xs={12}>
              <Typography color="textSecondary" variant="body2">
                <FiIcons.FiActivity /> Status
              </Typography>
            </Grid>
            <Grid item md={8} xs={12}>
              <Typography color="textPrimary" variant="body2">
                <StackStatus status={environment.stack?.status} />
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
            key={environment.environmentUri}
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
              to={`/console/environments/${environment.environmentUri}`}
            >
              Learn More
            </Button>
          </Box>
        </Box>
      </Card>
    </Grid>
  );
};
EnvironmentListItem.propTypes = {
  environment: PropTypes.object.isRequired
};
