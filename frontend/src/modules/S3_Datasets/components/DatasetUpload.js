import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Divider,
  LinearProgress,
  Switch,
  TextField,
  Typography
} from '@mui/material';
import axios from 'axios';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import { useState } from 'react';
import { FileDropzone } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';

import { getDatasetPresignedUrl, startGlueCrawler } from '../services';

export const DatasetUpload = (props) => {
  const { dataset, isAdmin } = props;
  const client = useClient();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const [prefix, setPrefix] = useState('raw');
  const [isUploading, setIsUploading] = useState(false);
  const [startCrawler, setStartCrawler] = useState(true);
  const [progress, setProgress] = useState(0);
  const [files, setFiles] = useState([]);

  const handleDrop = (newFiles) => {
    setFiles((prevFiles) => [...prevFiles, ...newFiles]);
  };

  const handleRemove = (file) => {
    setFiles((prevFiles) =>
      prevFiles.filter((_file) => _file.path !== file.path)
    );
  };

  const handleRemoveAll = () => {
    setFiles([]);
  };

  const runCrawler = async () => {
    const response = await client.mutate(
      startGlueCrawler({
        datasetUri: dataset.datasetUri,
        input: { prefix }
      })
    );
    if (!response.errors) {
      enqueueSnackbar('Crawler started', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  const fileUpload = async (file) => {
    const response = await client.query(
      getDatasetPresignedUrl({
        datasetUri: dataset.datasetUri,
        input: {
          fileName: file.name,
          prefix
        }
      })
    );
    if (!response.errors) {
      const presignedUrlResponse = JSON.parse(
        response.data.getDatasetPresignedUrl
      );
      const { url } = presignedUrlResponse;
      const { fields } = presignedUrlResponse;
      const formData = new FormData();
      Object.keys(fields).forEach((formFieldName) => {
        formData.append(formFieldName, fields[formFieldName]);
      });
      formData.append('file', file);

      const config = {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Access-Control-Allow-Methods':
            'GET, POST, PUT, DELETE, PATCH, OPTIONS',
          'Access-Control-Allow-Headers':
            'X-Requested-With, content-type, Authorization'
        },
        withCredentials: false,
        onUploadProgress: (e) => {
          setProgress(Math.round((e.loaded * 100) / e.total));
        }
      };
      setIsUploading(true);
      await axios
        .post(url, formData, config)
        .then(() => {
          enqueueSnackbar('File uploaded to S3', {
            anchorOrigin: {
              horizontal: 'right',
              vertical: 'top'
            },
            variant: 'success'
          });
        })
        .catch((e) => {
          dispatch({
            type: SET_ERROR,
            error: `Failed to upload: ${e.message}.`
          });
        });
      setTimeout(() => {
        setIsUploading(false);
        setFiles([]);
      }, 1000);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };
  const multiFilesUpload = async () => {
    await files.map((file) => fileUpload(file));
    if (startCrawler) {
      runCrawler().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  };

  return (
    <Box sx={{ mt: 2 }}>
      {isAdmin && (
        <Card>
          <CardHeader title="S3 Upload" />
          <Divider />
          <CardContent>
            <Box>
              <Typography
                color="textPrimary"
                gutterBottom
                variant="subtitle2"
                sx={{ mb: 2 }}
              >
                Prefix
              </Typography>
              <TextField
                fullWidth
                helperText="Prefix without trailing slash at the end (e.g raw not raw/)"
                label={`s3://${dataset.restricted.S3BucketName}/`}
                name="label"
                variant="outlined"
                value={prefix}
                onChange={(e) => {
                  setPrefix(e.target.value);
                }}
              />
            </Box>
            <Box sx={{ mt: 2 }}>
              <Typography color="textPrimary" gutterBottom variant="subtitle2">
                Infer Schema
              </Typography>
              <Typography color="textSecondary" variant="body2">
                Enabling this will automatically start a crawler to infer your
                file schema
              </Typography>
              <Switch
                color="primary"
                defaultChecked
                onChange={() => {
                  setStartCrawler(!startCrawler);
                }}
                edge="start"
                name="startCrawler"
              />
            </Box>

            <Box sx={{ mt: 2 }}>
              <Box />
              <FileDropzone
                files={files}
                maxFiles={1}
                onDrop={handleDrop}
                onRemove={handleRemove}
                onRemoveAll={handleRemoveAll}
                onUpload={multiFilesUpload}
              />
            </Box>

            {isUploading && (
              <Box
                sx={{
                  mt: 2
                }}
              >
                <LinearProgress variant="determinate" value={progress} />
              </Box>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

DatasetUpload.propTypes = {
  dataset: PropTypes.object.isRequired,
  isAdmin: PropTypes.bool.isRequired
};
