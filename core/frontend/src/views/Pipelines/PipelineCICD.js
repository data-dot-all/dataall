import PropTypes from 'prop-types';
import { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Divider,
  IconButton,
  List,
  ListItem,
  Chip,
  Typography
} from '@mui/material';
import { LoadingButton } from '@mui/lab';
import { CopyToClipboard } from 'react-copy-to-clipboard/lib/Component';
import { CopyAll } from '@mui/icons-material';
import { useTheme } from '@mui/styles';
import { useSnackbar } from 'notistack';
import useClient from '../../hooks/useClient';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import getDataPipelineCredsLinux from '../../api/DataPipeline/getDataPipelineCredsLinux';
import ChipInput from "../../components/TagsInput";
import Label from "../../components/Label";

const PipelineCICD = (props) => {
  const { pipeline } = props;
  const client = useClient();
  const theme = useTheme();
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const [loadingCreds, setLoadingCreds] = useState(false);

  const copyNotification = () => {
    enqueueSnackbar('Copied to clipboard', {
      anchorOrigin: {
        horizontal: 'right',
        vertical: 'top'
      },
      variant: 'success'
    });
  };

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
      <CardHeader title="CICD" />
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
              CICD Environment
            </Typography>
            <Typography color="textPrimary" variant="body2">
              {pipeline.environment.label}
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
              AWS Account
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
              Team
            </Typography>
            <Typography color="textPrimary" variant="body2">
              {pipeline.SamlGroupName}
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
            <Typography color="textPrimary" variant="subtitle2">
              <CopyToClipboard
                onCopy={() => copyNotification()}
                text={`git clone codecommit::${pipeline.environment.region}:${'//'}${pipeline.repo}`}
              >
                <IconButton>
                  <CopyAll
                    sx={{
                      color:
                        theme.palette.mode === 'dark'
                          ? theme.palette.primary.contrastText
                          : theme.palette.primary.main
                    }}
                  />
                </IconButton>
              </CopyToClipboard>
              {`git clone codecommit::${pipeline.environment.region}:${'//'}${pipeline.repo}`}
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

PipelineCICD.propTypes = {
  // @ts-ignore
  pipeline: PropTypes.object.isRequired
};

export default PipelineCICD;
