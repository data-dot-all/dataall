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
import * as FaIcons from 'react-icons/fa';
import { MdShowChart } from 'react-icons/md';
import { useNavigate } from 'react-router';
import { Link as RouterLink } from 'react-router-dom';
import { IconAvatar, Label, UpVotesReadOnly, useCardStyle } from 'design';

export const DashboardListItem = (props) => {
  const { dashboard } = props;
  const classes = useCardStyle();
  const navigate = useNavigate();
  return (
    <Grid item key={dashboard.dashboardUri} md={3} xs={12} {...props}>
      <Card key={dashboard.dashboardUri} className={classes.card} raised>
        <Box sx={{ p: 2 }}>
          <Box
            sx={{
              alignItems: 'center',
              display: 'flex'
            }}
          >
            <IconAvatar icon={<MdShowChart size={20} />} />
            <Box sx={{ ml: 2 }}>
              <Link
                underline="hover"
                component="button"
                color="textPrimary"
                variant="h6"
                onClick={() => {
                  navigate(`/console/dashboards/${dashboard.dashboardUri}`);
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
                <Tooltip title={dashboard.label}>
                  <span>{dashboard.label}</span>
                </Tooltip>
              </Link>
              <Typography color="textSecondary" variant="body2">
                by{' '}
                <Link underline="hover" color="textPrimary" variant="subtitle2">
                  {dashboard.owner}
                </Link>
              </Typography>
            </Box>
          </Box>
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
            <Tooltip title={dashboard.description || 'No description provided'}>
              <span>{dashboard.description || 'No description provided'}</span>
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
              <Typography color="textPrimary" variant="body2">
                <Label
                  color={
                    dashboard.userRoleForDashboard === 'Creator'
                      ? 'primary'
                      : 'info'
                  }
                >
                  {dashboard.userRoleForDashboard || '-'}
                </Label>
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
                <Tooltip title={dashboard.SamlGroupName || '-'}>
                  <span>{dashboard.SamlGroupName || '-'}</span>
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
                {dashboard.restricted.AwsAccountId}
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
                {dashboard.restricted.region}
              </Typography>
            </Grid>
          </Grid>
        </Box>
        <Box
          sx={{
            px: 3,
            py: 0.5
          }}
        />
        <Box
          sx={{
            px: 3,
            py: 1
          }}
        >
          <Grid
            alignItems="center"
            container
            key={dashboard.dashboardUri}
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
              to={`/console/dashboards/${dashboard.dashboardUri}`}
            >
              Learn More
            </Button>
          </Box>
          <Box sx={{ flexGrow: 1 }} />
          <UpVotesReadOnly upvotes={dashboard.upvotes} />
        </Box>
      </Card>
    </Grid>
  );
};
DashboardListItem.propTypes = {
  dashboard: PropTypes.object.isRequired
};
