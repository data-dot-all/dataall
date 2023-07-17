import {
  Box,
  Button,
  Card,
  CardHeader,
  Divider,
  Grid,
  Link,
  Typography
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import PropTypes from 'prop-types';
import ShareStatus from '../../components/ShareStatus';
import TextAvatar from '../../components/TextAvatar';
import useCardStyle from '../../hooks/useCardStyle';

const ShareInboxListItem = (props) => {
  const { share, reload } = props;
  const classes = useCardStyle();

  return (
    <Card
      key={share.shareUri}
      className={classes.card}
      sx={{
        mt: 2
      }}
    >
      <Grid container spacing={2} alignItems="center">
        <Grid item md={9} xs={6}>
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
                    to={`/console/datasets/${share.dataset.datasetUri}`}
                  >
                    {share.dataset.datasetName}
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
            <Typography color="textSecondary" variant="body1">
              {`Read access to Dataset: ${share.dataset.datasetName} 
                for Principal: ${share.principal.principalName} 
                from Environment: ${share.principal.environmentName}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="flex-end" md={3} xs={6} spacing={2}>
            <Box
                sx={{
                  alignItems: 'center',
                  display: 'flex',
                  pt: 3,
                  pb: 0.5
                }}
            >
              <Typography color="textPrimary" variant="body2">
                {`Currently shared items: ${share.statistics.sharedItems}`}
              </Typography>
            </Box>
            <Box
                sx={{
                  alignItems: 'center',
                  display: 'flex',
                  py: 0.5,
                }}
            >
              <Typography color="textPrimary" variant="body2">
                {`Revoked items: ${share.statistics.revokedItems}`}
              </Typography>
            </Box>
            <Box
                sx={{
                  alignItems: 'center',
                  display: 'flex',
                  py: 0.5,
                }}
            >
              <Typography color="textPrimary" variant="body2">
                {`Failed items: ${share.statistics.failedItems}`}
              </Typography>
            </Box>
            <Box
                sx={{
                  alignItems: 'center',
                  display: 'flex',
                  py: 0.5
                }}
            >
              <Typography color="textPrimary" variant="body2">
                {`Pending items: ${share.statistics.pendingItems}`}
              </Typography>
            </Box>
        </Grid>
      </Grid>
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
            to={`/console/shares/${share.shareUri}`}
          >
            Learn More
          </Button>
        </Box>
      </Box>
    </Card>
  );
};
ShareInboxListItem.propTypes = {
  share: PropTypes.object.isRequired,
  reload: PropTypes.func.isRequired
};
export default ShareInboxListItem;
