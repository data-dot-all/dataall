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
import { BlockOutlined, CheckCircleOutlined } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import { useSnackbar } from 'notistack';
import { useState } from 'react';
import ShareStatus from '../../components/ShareStatus';
import TextAvatar from '../../components/TextAvatar';
import { useDispatch } from '../../store';
import useClient from '../../hooks/useClient';
import approveShareObject from '../../api/ShareObject/approveShareObject';
import { SET_ERROR } from '../../store/errorReducer';
import rejectShareObject from '../../api/ShareObject/rejectShareObject';
import useCardStyle from '../../hooks/useCardStyle';

const ShareInboxListItem = (props) => {
  const { share, reload } = props;
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const client = useClient();
  const classes = useCardStyle();
  const [accepting, setAccepting] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const accept = async () => {
    setAccepting(true);
    const response = await client.mutate(
      approveShareObject({
        shareUri: share.shareUri
      })
    );
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
    const response = await client.mutate(
      rejectShareObject({
        shareUri: share.shareUri
      })
    );
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
      className={classes.card}
      sx={{
        mt: 2
      }}
    >
      <Grid container>
        <Grid item md={share.status === 'PendingApproval' ? 9 : 10} xs={6}>
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
                for the Principal: ${share.principal.principalName} 
                from Environment: ${share.principal.environmentName}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item md={share.status === 'PendingApproval' ? 3 : 2} xs={6}>
          {share.userRoleForShareObject === 'Approvers' &&
            share.status === 'PendingApproval' && (
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
          {share.userRoleForShareObject === 'Approvers' &&
            share.status === 'Approved' && (
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
