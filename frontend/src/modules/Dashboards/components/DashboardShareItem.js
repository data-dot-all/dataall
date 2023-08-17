import { BlockOutlined, CheckCircleOutlined } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import {
  Box,
  Card,
  CardHeader,
  Divider,
  Grid,
  Link,
  Typography
} from '@mui/material';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import { useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { ShareStatus, TextAvatar } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { approveDashboardShare, rejectDashboardShare } from '../services';

export const DashboardShareItem = (props) => {
  const { share, dashboard, reload } = props;
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const client = useClient();
  const [accepting, setAccepting] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const accept = async () => {
    setAccepting(true);
    const response = await client.mutate(approveDashboardShare(share.shareUri));
    if (!response.errors) {
      enqueueSnackbar('Share request approved', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      await reload();
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setAccepting(false);
  };

  const reject = async () => {
    setRejecting(true);
    const response = await client.mutate(rejectDashboardShare(share.shareUri));
    if (!response.errors) {
      enqueueSnackbar('Share request rejected', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      await reload();
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setRejecting(false);
  };
  return (
    <Card
      key={share.shareUri}
      sx={{
        mt: 2
      }}
    >
      <Grid container>
        <Grid item md={share.status === 'REQUESTED' ? 9 : 10} xs={6}>
          <CardHeader
            avatar={<TextAvatar name={share.owner} />}
            disableTypography
            subheader={
              <Box
                sx={{
                  alignItems: 'center',
                  display: 'flex',
                  flexWrap: 'wrap',
                  mt: 1
                }}
              >
                <Box
                  sx={{
                    alignItems: 'center',
                    display: 'flex',
                    mr: 1
                  }}
                >
                  <ShareStatus status={share.status} />
                </Box>
                <Typography color="textSecondary" variant="body2">
                  | For{' '}
                  <Link
                    underline="hover"
                    component={RouterLink}
                    color="textPrimary"
                    variant="subtitle2"
                    to={`/console/dashboards/${share.dashboardUri}`}
                  >
                    {dashboard.label}
                  </Link>{' '}
                  | {share.created}
                </Typography>
              </Box>
            }
            title={
              <Link underline="hover" color="textPrimary" variant="subtitle2">
                {share.owner}
              </Link>
            }
          />
          <Box
            sx={{
              pb: 2,
              px: 3
            }}
          >
            {share.status === 'APPROVED' && (
              <Typography color="textSecondary" variant="body1">
                {`Dashboard ${dashboard.label} access
                  approved for the team ${share.SamlGroupName || '-'}.`}
              </Typography>
            )}
            {share.status === 'REQUESTED' && (
              <Typography color="textSecondary" variant="body1">
                {`Approving will grant the team ${share.SamlGroupName || '-'}
                   access to dashboard ${dashboard.label}.`}
              </Typography>
            )}
            {share.status === 'REJECTED' && (
              <Typography color="textSecondary" variant="body1">
                {`Access to dashboard ${dashboard.label}
                  was rejected for the team ${share.SamlGroupName || '-'}.`}
              </Typography>
            )}
          </Box>
        </Grid>
        <Grid item md={share.status === 'REQUESTED' ? 3 : 2} xs={6}>
          {(dashboard.userRoleForDashboard === 'Creator' ||
            dashboard.userRoleForDashboard === 'Admin') &&
            share.status === 'REQUESTED' && (
              <Box sx={{ ml: 7 }}>
                <LoadingButton
                  loading={accepting}
                  color="success"
                  startIcon={<CheckCircleOutlined />}
                  sx={{ mt: 6, mb: 1, mr: 1 }}
                  onClick={accept}
                  type="button"
                  variant="outlined"
                >
                  Approve
                </LoadingButton>
                <LoadingButton
                  loading={rejecting}
                  color="error"
                  sx={{ mt: 6, mb: 1 }}
                  startIcon={<BlockOutlined />}
                  onClick={reject}
                  type="button"
                  variant="outlined"
                >
                  Reject
                </LoadingButton>
              </Box>
            )}
          {(dashboard.userRoleForDashboard === 'Creator' ||
            dashboard.userRoleForDashboard === 'Admin') &&
            share.status === 'APPROVED' && (
              <LoadingButton
                loading={rejecting}
                color="error"
                startIcon={<BlockOutlined />}
                sx={{ mt: 6, mb: 3 }}
                onClick={reject}
                type="button"
                variant="outlined"
              >
                Reject
              </LoadingButton>
            )}
        </Grid>
      </Grid>
      <Divider />
    </Card>
  );
};
DashboardShareItem.propTypes = {
  share: PropTypes.object.isRequired,
  dashboard: PropTypes.object.isRequired,
  reload: PropTypes.func.isRequired
};
