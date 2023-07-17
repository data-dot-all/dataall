/* import Markdown from 'react-markdown/with-html';
import { Box, Button, CircularProgress, Container, Paper } from '@mui/material';
import PropTypes from 'prop-types';
import { useEffect, useState } from 'react';
import { useSnackbar } from 'notistack';
import { styled } from '@mui/styles';
import { LoadingButton } from '@mui/lab';
import SimpleMDE from 'react-simplemde-editor';
import useClient from '../../hooks/useClient';
import { useDispatch } from '../../store';
import { SET_ERROR } from '../../store/errorReducer';
import getDatasetSummary from '../../api/Dataset/getDatasetSummary';
import saveDatasetSummary from '../../api/Dataset/saveDatasetSummary';
import PencilAlt from '../../icons/PencilAlt';

const MarkdownWrapper = styled('div')(({ theme }) => ({
  color: theme.palette.text.primary,
  fontFamily: theme.typography.fontFamily,
  '& p': {
    marginBottom: theme.spacing(2)
  }
}));
const DatasetSummary = (props) => {
  const { dataset } = props;
  const client = useClient();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const [content, setContent] = useState('');
  const [isEditorMode, setIsEditorMode] = useState(false);
  const [ready, setReady] = useState(false);
  // const canEdit = ['BusinessOwner', 'Admin', 'DataSteward', 'Creator'].indexOf(dataset.userRoleForDataset) != -1;

  const handleChange = (value) => {
    setContent(value);
  };
  const fetchSummary = async () => {
    setReady(false);
    const response = await client.query(getDatasetSummary(dataset.datasetUri));
    if (!response.errors) {
      setContent(response.data.getDatasetSummary === '' ? 'No content found' : response.data.getDatasetSummary);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setReady(true);
  };

  const saveSummary = async () => {
    const response = await client.mutate(saveDatasetSummary({ datasetUri: props.dataset.datasetUri, content }));
    if (!response.errors) {
      enqueueSnackbar('Dataset summary saved', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      setIsEditorMode(false);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };
  useEffect(() => {
    if (client) {
      fetchSummary().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client]);

  if (!ready) {
    return <CircularProgress />;
  }
  return (
    <Box>
      <Box
        display="flex"
        justifyContent="flex-end"
        sx={{ p: 1 }}
      >
        {!isEditorMode && (
        <Button
          color="primary"
          startIcon={<PencilAlt />}
          sx={{ m: 1 }}
          variant="outlined"
          onClick={() => setIsEditorMode(true)}
        >
          Edit
        </Button>
        )}
      </Box>
      {!isEditorMode && (
      <Paper
        sx={{ mt: 1 }}
        variant="outlined"
      >
        <Box sx={{ py: 3 }}>
          <Container maxWidth="md">
            <MarkdownWrapper>
              <Markdown
                skipHtml
                source={content}
              />
            </MarkdownWrapper>
          </Container>
        </Box>
      </Paper>
      )}

      {isEditorMode && (
      <Box>
        <Paper
          sx={{ mt: 3, height: '100vh' }}
          variant="outlined"
        >
          <SimpleMDE
            value={content}
            onChange={handleChange}
          />

        </Paper>
        {isEditorMode && (
        <Box
          display="flex"
          justifyContent="flex-end"
          sx={{ p: 1 }}
        >
          <LoadingButton
            color="primary"
            sx={{ m: 1 }}
            onClick={saveSummary}
            variant="outlined"
          >
            Save
          </LoadingButton>
          <Button
            color="primary"
            sx={{ m: 1 }}
            variant="outlined"
            onClick={() => setIsEditorMode(false)}
          >
            Cancel
          </Button>
        </Box>
        )}

      </Box>

      )}
    </Box>
  );
};

DatasetSummary.propTypes = {
  dataset: PropTypes.object.isRequired
};

export default DatasetSummary; */
