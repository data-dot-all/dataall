import { Box, Button, Card, Grid, Tooltip, Typography } from '@mui/material';
import PropTypes from 'prop-types';
import { Link as RouterLink } from 'react-router-dom';
import { ShareStatus, useCardStyle } from 'design';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';

export const ShareBoxListItem = ({ share }) => {
  const classes = useCardStyle();

  return (
    <Card
      key={share.shareUri}
      className={classes.card}
      sx={{
        mt: 2
      }}
    >
      <Grid container spacing={0.5} alignItems="center">
        <Grid item justifyContent="center" md={2.2} lg={1.5} xl={1.2}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <ShareStatus status={share.status} />
          </Box>
        </Grid>
        <Grid item justifyContent="flex-end" md={2} lg={2.25} xl={2.25}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Typography color="textPrimary" variant="body1">
              Request owner
            </Typography>
            <Typography
              color="textSecondary"
              variant="body1"
              style={{ wordWrap: 'break-word' }}
            >
              {`${share.principal.SamlGroupName}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="flex-end" md={2} lg={2.25} xl={2.25}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Typography color="textPrimary" variant="body1">
              IAM role name
            </Typography>
            <Typography
              color="textSecondary"
              variant="body1"
              style={{ wordWrap: 'break-word' }}
            >
              {`${share.principal.principalIAMRoleName}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="center" md={2} lg={2.25} xl={2.25}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Typography color="textPrimary" variant="body1">
              Dataset
            </Typography>
            <Typography
              color="textSecondary"
              variant="body1"
              style={{ wordWrap: 'break-word' }}
            >
              {`${share.dataset.datasetName}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="center" md={2} lg={2.25} xl={2.25}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Typography
              color="textPrimary"
              variant="body1"
              style={{ wordWrap: 'break-word' }}
            >
              Dataset Owner
            </Typography>
            <Typography color="textSecondary" variant="body1">
              {`${share.dataset.SamlAdminGroupName}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="flex-end" md={1.3} lg={1.2} xl={1.4}>
          <Button
            color="primary"
            type="button"
            component={RouterLink}
            to={`/console/shares/${share.shareUri}`}
            variant="contained"
          >
            Open Share Request
          </Button>
        </Grid>
        <Grid item justifyContent="flex-end" md={0.2} lg={0.2} xl={0.4}>
          {share.statistics.sharedItems > 0 && (
            <Tooltip
              title={share.statistics.sharedItems + ' shared items'}
              placement="right"
            >
              <CheckCircleIcon color={'success'} />
            </Tooltip>
          )}
          {share.statistics.failedItems > 0 && (
            <Tooltip
              title={share.statistics.failedItems + ' failed items'}
              placement="right"
            >
              <ErrorIcon color={'error'} />
            </Tooltip>
          )}
        </Grid>
      </Grid>
    </Card>
  );
};
ShareBoxListItem.propTypes = {
  share: PropTypes.object.isRequired
};
