import { CopyAll } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import { useState } from 'react';
import { FaExternalLinkAlt } from 'react-icons/fa';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { generateDatasetAccessToken } from '../services';
import { getDatasetAssumeRoleUrl, useClient } from 'services';

export const DatasetAWSActions = (props) => {
  const { dataset, isAdmin } = props;

  const client = useClient();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const [isLoadingUI, setIsLoadingUI] = useState(false);
  const [loadingCreds, setLoadingCreds] = useState(false);
  const generateCredentials = async () => {
    setLoadingCreds(true);
    const response = await client.mutate(
      generateDatasetAccessToken(dataset.datasetUri)
    );
    if (!response.errors) {
      await navigator.clipboard.writeText(
        response.data.generateDatasetAccessToken
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

  const goToS3Console = async () => {
    setIsLoadingUI(true);
    const response = await client.query(
      getDatasetAssumeRoleUrl(dataset.datasetUri)
    );
    if (!response.errors) {
      window.open(response.data.getDatasetAssumeRoleUrl, '_blank');
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setIsLoadingUI(false);
  };

  return (
    <>
      {isAdmin && (
        <>
          <LoadingButton
            loading={loadingCreds}
            color="primary"
            startIcon={<CopyAll size={15} />}
            sx={{ mt: 1, mr: 1 }}
            variant="outlined"
            onClick={generateCredentials}
          >
            AWS Credentials
          </LoadingButton>
          <LoadingButton
            loading={isLoadingUI}
            startIcon={<FaExternalLinkAlt size={15} />}
            sx={{ mt: 1, mr: 1 }}
            variant="outlined"
            onClick={goToS3Console}
          >
            S3 Bucket
          </LoadingButton>
        </>
      )}
    </>
  );
};

DatasetAWSActions.propTypes = {
  dataset: PropTypes.object.isRequired,
  isAdmin: PropTypes.bool.isRequired
};
