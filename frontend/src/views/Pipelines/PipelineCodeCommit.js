import PropTypes from 'prop-types';
import { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Divider,
  List,
  ListItem,
  Typography
} from '@mui/material';
import { LoadingButton } from '@mui/lab';
import { CopyAll } from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import useClient from '../../hooks/useClient';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import getSqlPipelineCredsLinux from '../../api/SqlPipeline/getSqlPipelineCredsLinux';

const PipelineCodeCommit = (props) => {
  const { pipeline } = props;
  const client = useClient();
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const [loadingCreds, setLoadingCreds] = useState(false);

  const generateCredentials = async () => {
    setLoadingCreds(true);
    const response = await client.query(
      getSqlPipelineCredsLinux(pipeline.sqlPipelineUri)
    );
    if (!response.errors) {
      await navigator.clipboard.writeText(
        response.data.getSqlPipelineCredsLinux
      );
      enqueueSnackbar('Credentials copied to clipboard', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoadingCreds(false);
  };

  return (
    <Card {...pipeline}>
      <CardHeader title="AWS CodeCommit" />
      <Divider />
      <CardContent sx={{ pt: 0 }}>
        <List>
          <ListItem
            disableGutters
            divider
            sx={{
              justifyContent: 'space-between',
              padding: 2
            }}
          >
            <Typography color="textSecondary" variant="subtitle2">
              Account
            </Typography>
            <Typography color="textPrimary" variant="body2">
              {pipeline.environment.AwsAccountId}
            </Typography>
          </ListItem>
          <ListItem
            disableGutters
            divider
            sx={{
              justifyContent: 'space-between',
              padding: 2
            }}
          >
            <Typography color="textSecondary" variant="subtitle2">
              Region
            </Typography>
            <Typography color="textPrimary" variant="body2">
              {pipeline.environment.region}
            </Typography>
          </ListItem>
          <ListItem
            disableGutters
            divider
            sx={{
              justifyContent: 'space-between',
              padding: 2
            }}
          >
            <Typography color="textSecondary" variant="subtitle2">
              Repository name
            </Typography>
            <Typography color="textPrimary" variant="body2">
              {pipeline.repo}
            </Typography>
          </ListItem>
          <ListItem
            disableGutters
            divider
            sx={{
              justifyContent: 'space-between',
              padding: 2
            }}
          >
            <Typography color="textSecondary" variant="subtitle2">
              Git clone
            </Typography>
            <Typography color="textPrimary" variant="body2">
              {`git clone codecommit::${pipeline.environment.region}:${'//'}${
                pipeline.repo
              }`}
            </Typography>
          </ListItem>
        </List>
      </CardContent>
      <CardContent>
        <Box
          sx={{
            alignItems: 'flex-start',
            display: 'flex'
          }}
        >
          <LoadingButton
            loading={loadingCreds}
            color="primary"
            startIcon={<CopyAll size={15} />}
            sx={{ mr: 1 }}
            variant="outlined"
            onClick={generateCredentials}
          >
            AWS Credentials
          </LoadingButton>
        </Box>
      </CardContent>
    </Card>
  );
};

PipelineCodeCommit.propTypes = {
  // @ts-ignore
  pipeline: PropTypes.object.isRequired
};

export default PipelineCodeCommit;
