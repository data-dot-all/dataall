import { Box, Button, Card, Grid, Typography } from '@mui/material';
import PropTypes from 'prop-types';
import { Link as RouterLink } from 'react-router-dom';
import { ShareStatus, useCardStyle } from 'design';

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
      <Grid container spacing={1} alignItems="center">
        <Grid item justifyContent="center" md={1} xs={1}>
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
        <Grid item justifyContent="flex-end" md={5} xs={5}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Typography color="textPrimary" variant="body1">
              {`Request owner [principal]`}
            </Typography>
            <Typography color="textSecondary" variant="body1">
              {`${share.principal.principalName}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="center" md={2} xs={2}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Typography color="textPrimary" variant="body1">
              {`Dataset`}
            </Typography>
            <Typography color="textSecondary" variant="body1">
              {`${share.dataset.datasetName}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="center" md={2} xs={2}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Typography color="textPrimary" variant="body1">
              {`Dataset Owner`}
            </Typography>
            <Typography color="textSecondary" variant="body1">
              {`${share.dataset.SamlAdminGroupName}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="flex-end" md={1.5} xs={1.5}>
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
      </Grid>
    </Card>
  );
};
ShareBoxListItem.propTypes = {
  share: PropTypes.object.isRequired,
  reload: PropTypes.func.isRequired
};
