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
import { useNavigate } from 'react-router';
import { LoadingButton } from '@mui/lab';
import { CheckCircleOutlined } from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { useState } from 'react';
import ShareStatus from '../../components/ShareStatus';
import TextAvatar from '../../components/TextAvatar';
import { useDispatch } from '../../store';
import useClient from '../../hooks/useClient';
import { SET_ERROR } from '../../store/errorReducer';
import submitApproval from '../../api/ShareObject/submitApproval';
import PencilAltIcon from '../../icons/PencilAlt';

const ShareOutboxListItem = (props) => {
  const { share, reload } = props;
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const client = useClient();
  const [submitting, setSubmitting] = useState(false);
  const submit = async () => {
    setSubmitting(true);
    const response = await client.mutate(
      submitApproval({
        shareUri: share.shareUri
      })
    );
    if (!response.errors) {
      enqueueSnackbar('Share request submitted', {
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
    setSubmitting(false);
  };
  return (
    <Card
      key={share.shareUri}
      sx={{
        mt: 2
      }}
    >
      <Grid container>
        <Grid item md={10} xs={6}>
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
        <Grid item md={2} xs={6}>
          {(share.status === 'PendingApproval' ||
            share.status === 'Approved') && (
            <Box sx={{ ml: 7 }}>
              <LoadingButton
                color="primary"
                startIcon={<PencilAltIcon fontSize="small" />}
                sx={{ mt: 6, mb: 1, mr: 1 }}
                onClick={() => navigate(`/console/shares/${share.shareUri}`)}
                type="button"
                variant="outlined"
              >
                Update
              </LoadingButton>
            </Box>
          )}
          {share.status === 'Draft' && (
            <Box sx={{ ml: 7 }}>
              <LoadingButton
                loading={submitting}
                color="success"
                startIcon={<CheckCircleOutlined />}
                sx={{ mt: 6, mb: 1, mr: 1 }}
                onClick={submit}
                type="button"
                variant="outlined"
              >
                Submit
              </LoadingButton>
            </Box>
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
ShareOutboxListItem.propTypes = {
  share: PropTypes.object.isRequired,
  reload: PropTypes.func.isRequired
};
export default ShareOutboxListItem;
