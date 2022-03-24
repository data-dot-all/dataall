import PropTypes from 'prop-types';
import { useState } from 'react';
import { useSnackbar } from 'notistack';
import { FaExternalLinkAlt } from 'react-icons/all';
import { LoadingButton } from '@material-ui/lab';
import { CopyAll } from '@material-ui/icons';
import useClient from '../../hooks/useClient';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import getDatasetAdminConsoleUrl from '../../api/Dataset/getDatasetAdminConsoleUrl';
import generateDatasetAccessToken from '../../api/Dataset/generateDatasetAccessToken';

function DatasetAWSActions({ dataset, isAdmin }) {
  const client = useClient();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const [isLoadingUI, setIsLoadingUI] = useState(false);
  const [loadingCreds, setLoadingCreds] = useState(false);
  const generateCredentials = async () => {
    setLoadingCreds(true);
    const response = await client.mutate(generateDatasetAccessToken(dataset.datasetUri));
    if (!response.errors) {
      await navigator.clipboard.writeText(response.data.generateDatasetAccessToken);
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
    const response = await client.query(getDatasetAdminConsoleUrl(dataset.datasetUri));
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
            pending={loadingCreds}
            color="primary"
            startIcon={<CopyAll size={15} />}
            sx={{ mt: 1, mr: 1 }}
            variant="outlined"
            onClick={generateCredentials}
          >
            AWS Credentials
          </LoadingButton>
          <LoadingButton
            pending={isLoadingUI}
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
}

DatasetAWSActions.propTypes = {
  dataset: PropTypes.object.isRequired,
  isAdmin: PropTypes.bool.isRequired
};

export default DatasetAWSActions;
