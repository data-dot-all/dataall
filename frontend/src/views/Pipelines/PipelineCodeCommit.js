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
  Chip,
  Typography
} from '@mui/material';
import { LoadingButton } from '@mui/lab';
import { CopyAll } from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import useClient from '../../hooks/useClient';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import getDataPipelineCredsLinux from '../../api/DataPipeline/getDataPipelineCredsLinux';
import ChipInput from "../../components/TagsInput";
import Label from "../../components/Label";

const PipelineCodeCommit = (props) => {
  const { pipeline } = props;
  const client = useClient();
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const [loadingCreds, setLoadingCreds] = useState(false);

  const generateCredentials = async () => {
    setLoadingCreds(true);
    const response = await client.query(
      getDataPipelineCredsLinux(pipeline.DataPipelineUri)
    );
    if (!response.errors) {
      await navigator.clipboard.writeText(
        response.data.getDataPipelineCredsLinux
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
      <CardHeader title="AWS CICD Pipeline" />
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
              Development Strategy
            </Typography>
            <Typography color="textPrimary" variant="body2">
              {pipeline.devStrategy}
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
        <Box>
            <Box sx={{ mt: 3 }}>
              <Typography color="textSecondary" variant="subtitle2">
                Development stages
              </Typography>
              <Box sx={{ mt: 1 }}>
                {pipeline.devStages?.map((stage) => (
                  <Chip
                    sx={{ mr: 0.5, mb: 0.5 }}
                    key={stage}
                    label={stage}
                    variant="outlined"
                  />
                ))}
              </Box>
            </Box>
        </Box>
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
