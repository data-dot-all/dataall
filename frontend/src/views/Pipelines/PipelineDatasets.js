import {
  Card,
  CardContent,
  CardHeader,
  Divider,
  List,
  ListItem,
  Typography
} from '@mui/material';
import PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';
import { SET_ERROR, useDispatch } from '../../globalErrors';
import { getDataset, useClient } from '../../services';

const PipelineDatasets = (props) => {
  const { pipeline } = props;
  const client = useClient();
  const dispatch = useDispatch();
  const [inputDataset, setInputDataset] = useState('');
  const [outputDataset, setOutputDataset] = useState('');

  const fetchDatasets = useCallback(async () => {
    if (pipeline.inputDatasetUri) {
      const response = await client.query(getDataset(pipeline.inputDatasetUri));
      if (!response.errors && response.data.getDataset !== null) {
        setInputDataset(response.data.getDataset.label);
      } else {
        const error = response.errors
          ? response.errors[0].message
          : 'Dataset not found';
        dispatch({ type: SET_ERROR, error });
      }
    }
    if (pipeline.outputDatasetUri) {
      const response = await client.query(
        getDataset(pipeline.outputDatasetUri)
      );
      if (!response.errors && response.data.getDataset !== null) {
        setOutputDataset(response.data.getDataset.label);
      } else {
        const error = response.errors
          ? response.errors[0].message
          : 'Dataset not found';
        dispatch({ type: SET_ERROR, error });
      }
    }
  }, [client, dispatch]);

  useEffect(() => {
    if (client) {
      fetchDatasets().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch, fetchDatasets]);

  return (
    <Card {...pipeline}>
      <CardHeader title="Parameters" />
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
              Input Dataset
            </Typography>
            <Typography color="textPrimary" variant="body2">
              {inputDataset}
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
              Output Dataset
            </Typography>
            <Typography color="textPrimary" variant="body2">
              {outputDataset}
            </Typography>
          </ListItem>
        </List>
      </CardContent>
    </Card>
  );
};

PipelineDatasets.propTypes = {
  // @ts-ignore
  pipeline: PropTypes.object.isRequired
};

export default PipelineDatasets;
