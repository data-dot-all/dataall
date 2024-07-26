// import { LoadingButton } from '@mui/lab';
import {
  // Autocomplete,
  Avatar,
  Box,
  Button,
  // CardContent,
  // CardHeader,
  Checkbox,
  Chip,
  Dialog,
  Divider,
  FormControl,
  FormGroup,
  FormControlLabel,
  FormLabel,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Switch,
  // TextField,
  Typography
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
// import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
// import { useCallback, useEffect, useState } from 'react';
import { useState } from 'react';
import AutoModeIcon from '@mui/icons-material/AutoMode';
// import * as Yup from 'yup';
// import { ChipInput, Defaults } from 'design';
import { Scrollbar } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
/* eslint-disable no-console */
export const GenerateMetadataModal = (props) => {
  const { dataset, onApply, onClose, open, ...other } = props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const [targetType, setTargetType] = useState('');
  const [targets, setTargets] = useState([]);
  const [targetOptions, setTargetOptions] = useState([]);
  const [version, setVersion] = useState(0);
  const [selectedMetadataTypes, setSelectedMetadataTypes] = useState({
    label: false,
    description: false,
    tags: false,
    topics: false
  });
  const [loadingMetadata, setLoadingMetadata] = useState(false);
  const [disabledGenerateButton, setDisabledGenerateButton] = useState(true);

  const handleChange = (event) => {
    console.log('handleChange', event);
    console.log('targetOptions', targetOptions);
    console.log('targets', targets);
    setTargetType(event.target.value);
    if (event.target.value === 'Dataset') {
      setTargets([
        {
          targetUri: dataset.datasetUri,
          targetType: 'S3_Dataset'
        }
      ]);
      setTargetOptions([
        {
          targetUri: dataset.datasetUri,
          targetType: event.target.value,
          name: dataset.name
        }
      ]);
    } else {
      setTargets([]);
      setTargetOptions([]); //TODO fetch tables and Folders
    }
  };

  const handleMetadataChange = (event) => {
    console.log('handleMetadataChange', event);
    setSelectedMetadataTypes({
      ...selectedMetadataTypes,
      [event.target.name]: event.target.checked
    });
    // Check if any metadata type is checked
    const isAnyMetadataTypeChecked = Object.values(selectedMetadataTypes).some(
      (value) => value === true
    );
    // TODO: there is something wrong with this, when we select 2 tabs
    setDisabledGenerateButton(isAnyMetadataTypeChecked);
  };

  const generateMetadata = async () => {
    setLoadingMetadata(true);
    for (let target of targets) {
      target.response = await client.mutate(
        generateMetadata(target.targetUri, target.targetType)
      );
      if (!target.response.errors) {
        enqueueSnackbar(
          `Returned response ${target.response.data.generateMetadata}`,
          {
            anchorOrigin: {
              horizontal: 'right',
              vertical: 'top'
            },
            variant: 'success'
          }
        );
      } else {
        dispatch({ type: SET_ERROR, error: target.response.errors[0].message });
      }
    }
    setVersion(version + 1);
    setLoadingMetadata(false);
  }; //TODO EDIT THIS CALL WITH INPUT/OUTPUT FROM BACKEND

  if (!dataset) {
    return null;
  }

  return (
    <Dialog maxWidth="lg" fullWidth onClose={onClose} open={open} {...other}>
      <Grid
        container
        sx={{ m: 1 }}
        spacing={3}
        justifyContent="flex-start"
        {...other}
      >
        <Grid item lg={2} xl={2} md={2} sm={2} xs={2}>
          <Chip
            avatar={<Avatar>1</Avatar>}
            label="Select target type"
            color="primary"
            variant="outlined"
          />
        </Grid>
        <Grid item lg={6} xl={6} md={6} sm={6} xs={6}>
          {targetType && (
            <Chip
              avatar={<Avatar>2</Avatar>}
              label="Select target resources"
              color="primary"
              variant="outlined"
            />
          )}
        </Grid>
        <Grid item lg={3} xl={3} md={3} sm={3} xs={3}>
          {targetType && !!targets.length && (
            <Chip
              avatar={<Avatar>3</Avatar>}
              label="Select type of metadata"
              color="primary"
              variant="outlined"
            />
          )}
        </Grid>
      </Grid>
      <Divider></Divider>
      <Grid
        container
        sx={{ mt: 1 }}
        spacing={3}
        justifyContent="space-around"
        alignItems="flex-start"
        {...other}
      >
        <Grid item lg={2} xl={2} md={2} sm={2} xs={2}>
          <FormControl sx={{ minWidth: 200, mb: 1 }}>
            <InputLabel id="Target">Target Type *</InputLabel>
            <Select
              id="demo-simple-select"
              value={targetType}
              label="Target Type *"
              onChange={handleChange}
            >
              <MenuItem value={'Dataset'}>Dataset</MenuItem>
              <MenuItem value={'TablesAndFolders'}>Tables and Folders</MenuItem>
            </Select>
          </FormControl>
          {targetType === 'Dataset' && (
            <Typography
              align="left"
              color="textSecondary"
              variant="subtitle2"
              sx={{ ml: 1 }}
            >
              Data.all will use the table and folder metadata to generate
              Dataset label, description, tags and/or topics using Amazon
              Bedrock.
            </Typography>
          )}
          {targetType === 'TablesAndFolders' && (
            <Typography //TODO: better info messages
              align="left"
              color="textSecondary"
              variant="subtitle2"
              sx={{ ml: 1 }}
            >
              Data.all will use table column names and table descriptions and
              folder S3 prefix names to generate Tables and Folders label,
              description, tags and/or topics using Amazon Bedrock.
            </Typography>
          )}
        </Grid>
        <Grid item lg={6} xl={6} md={6} sm={6} xs={6}>
          {targetType === 'Dataset' && (
            <FormControlLabel
              disabled
              control={<Checkbox checked />}
              label={dataset.name}
            />
          )}
          {targetType === 'TablesAndFolders' && (
            <Scrollbar>
              <Box sx={{ minWidth: 600 }}>
                <DataGrid
                  autoHeight
                  checkboxSelection
                  getRowId={(node) => node.targetUri}
                  rows={targetOptions}
                  columns={[
                    { field: 'targetUri', hide: true },
                    {
                      field: 'name',
                      headerName: 'Name',
                      flex: 1.5,
                      editable: false
                    },
                    {
                      field: 'targetType',
                      headerName: 'Type',
                      flex: 1,
                      editable: false
                    }
                  ]}
                  // rowCount={items.count}
                  // page={items.page - 1}
                  // pageSize={filter.pageSize}
                  // paginationMode="server"
                  // onPageChange={handlePageChange}
                  // loading={loading}
                  // onPageSizeChange={(pageSize) => {
                  //   setFilter({ ...filter, pageSize: pageSize });
                  // }}
                  getRowHeight={() => 'auto'}
                  disableSelectionOnClick
                  sx={{
                    wordWrap: 'break-word',
                    '& .MuiDataGrid-row': {
                      borderBottom: '1px solid rgba(145, 158, 171, 0.24)'
                    },
                    '& .MuiDataGrid-columnHeaders': {
                      borderBottom: 0.5
                    }
                  }}
                />
              </Box>
            </Scrollbar>
          )}
        </Grid>
        <Grid item lg={3} xl={3} md={3} sm={3} xs={3}>
          {targetType && !!targets.length && (
            <FormGroup>
              <FormLabel component="legend">Metadata</FormLabel>
              <FormControlLabel
                control={
                  <Switch
                    name="label"
                    checked={selectedMetadataTypes.label}
                    onChange={handleMetadataChange}
                  />
                }
                label="Label"
              />
              <FormControlLabel
                control={
                  <Switch
                    name="description"
                    checked={selectedMetadataTypes.description}
                    onChange={handleMetadataChange}
                  />
                }
                label="Description"
              />
              <FormControlLabel
                control={
                  <Switch
                    name="tags"
                    checked={selectedMetadataTypes.tags}
                    onChange={handleMetadataChange}
                  />
                }
                label="Tags"
              />
              <FormControlLabel
                control={
                  <Switch
                    name="topics"
                    checked={selectedMetadataTypes.topics}
                    onChange={handleMetadataChange}
                  />
                }
                label="Topics"
              />
            </FormGroup>
          )}
        </Grid>
      </Grid>
      {!loadingMetadata && (
        <Button
          color="primary"
          size="small"
          startIcon={<AutoModeIcon size={15} />}
          sx={{ m: 2 }}
          onClick={generateMetadata}
          type="button"
          variant="contained"
          disabled={disabledGenerateButton}
        >
          Generate
        </Button>
      )}
    </Dialog>
  );
};

GenerateMetadataModal.propTypes = {
  dataset: PropTypes.object.isRequired,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired
};
