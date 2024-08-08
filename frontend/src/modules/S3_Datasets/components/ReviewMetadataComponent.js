// import { LoadingButton } from '@mui/lab';
import {
  // Autocomplete,
  Button,
  // CardContent,
  // CardHeader,
  // Checkbox,
  Box,
  Chip,
  // Divider,
  // FormControl,
  // FormGroup,
  // FormControlLabel,
  // FormLabel,
  // Grid,
  // InputLabel,
  // MenuItem,
  // Select,
  // Switch,
  // TextField,
  Typography,
  CircularProgress
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
// import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import AutoModeIcon from '@mui/icons-material/AutoMode';
// import * as Yup from 'yup';
// import { ChipInput, Defaults } from 'design';
import { Scrollbar } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { updateDataset, generateMetadataBedrock } from '../services';
import { updateDatasetTable } from 'modules/Tables/services';
import { listSampleData } from '../services/listSampleData';
import { updateDatasetStorageLocation } from 'modules/Folders/services';
import SampleDataPopup from './SampleDataPopup';
import React, { useState } from 'react';
/* eslint-disable no-console */
export const ReviewMetadataComponent = (props) => {
  const {
    dataset,
    // targetType,
    targets,
    setTargets,
    selectedMetadataTypes,
    version
    // setVersion
  } = props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const [popupOpen, setPopupOpen] = useState(false);
  const [sampleData, setSampleData] = useState(null);
  const [targetUri, setTargetUri] = useState(null);
  const openPopup = (data) => {
    setSampleData(data);
    setPopupOpen(true);
  };

  const closePopup = () => {
    setPopupOpen(false);
    setSampleData(null);
  };
  async function handleRegenerate(table) {
    try {
      const response = await client.query(
        listSampleData({
          tableUri: table.targetUri
        })
      );
      console.log(response);
      openPopup(response.data.listSampleData);
      setTargetUri(table.targetUri);
      if (!response.errors) {
        enqueueSnackbar('Successfully read sample data', {
          variant: 'success'
        });
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (err) {
      dispatch({ type: SET_ERROR, error: err.message });
    }
  }
  const handleAcceptAndRegenerate = async () => {
    // Perform any necessary actions for accepting and regenerating the data
    console.log('Accept and Regenerate clicked');
    try {
      const targetIndex = targets.findIndex((t) => t.targetUri === targetUri);

      console.log(sampleData);
      if (targetIndex !== -1) {
        const { __typename, ...sampleDataWithoutTypename } = sampleData;
        const response = await client.mutate(
          generateMetadataBedrock({
            resourceUri: targets[targetIndex].targetUri,
            targetType: targets[targetIndex].targetType,
            metadataTypes: Object.entries(selectedMetadataTypes)
              .filter(([key, value]) => value === true)
              .map(([key]) => key),
            version: version, // You'll need to pass the `version` prop here
            sampleData: sampleDataWithoutTypename // You can pass the sample data here if needed
          })
        );

        if (!response.errors) {
          const updatedTarget = {
            ...targets[targetIndex],
            description: response.data.generateMetadata.description,
            label: response.data.generateMetadata.label,
            name: response.data.generateMetadata.name,
            tags: response.data.generateMetadata.tags,
            topics: response.data.generateMetadata.topics
          };

          const updatedTargets = [...targets];
          updatedTargets[targetIndex] = updatedTarget;

          setTargets(updatedTargets);

          enqueueSnackbar(
            `Metadata generation is successful for ${updatedTarget.name}`,
            {
              anchorOrigin: {
                horizontal: 'right',
                vertical: 'top'
              },
              variant: 'success'
            }
          );
        }
      } else {
        console.error(`Target with targetUri not found`);
        enqueueSnackbar(`Metadata generation is unsuccessful`, {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'error'
        });
      }

      closePopup(); // Close the popup after generating the metadata
    } catch (err) {
      dispatch({ type: SET_ERROR, error: err.message });
    }
  };

  async function saveMetadata(targets) {
    try {
      const updatedTargets = targets.map(async (target) => {
        const updatedMetadata = {};

        // Loop through selectedMetadataTypes and add the corresponding key-value pairs to updatedMetadata
        Object.entries(selectedMetadataTypes).forEach(
          ([metadataType, checked]) => {
            if (checked) {
              updatedMetadata[metadataType] = target[metadataType];
            }
          }
        );
        if (target.targetType === 'S3_Dataset') {
          updatedMetadata.KmsAlias = dataset.KmsAlias;
          const response = await client.mutate(
            updateDataset({
              datasetUri: target.targetUri, // Use target.targetUri instead of dataset.datasetUri
              input: updatedMetadata
            })
          );

          if (!response.errors) {
            return { ...target, success: true }; // Return the updated target with success flag
          } else {
            dispatch({ type: SET_ERROR, error: response.errors[0].message });
            return { ...target, success: false }; // Return the target with success flag set to false
          }
        } else if (target.targetType === 'Table') {
          const response = await client.mutate(
            updateDatasetTable({
              tableUri: target.targetUri, // Use target.targetUri instead of dataset.datasetUri
              input: updatedMetadata
            })
          );

          if (!response.errors) {
            return { ...target, success: true }; // Return the updated target with success flag
          } else {
            dispatch({ type: SET_ERROR, error: response.errors[0].message });
            return { ...target, success: false }; // Return the target with success flag set to false
          }
        } else if (target.targetType === 'Folder') {
          const response = await client.mutate(
            updateDatasetStorageLocation({
              locationUri: target.targetUri, // Use target.targetUri instead of dataset.datasetUri
              input: updatedMetadata
            })
          );

          if (!response.errors) {
            return { ...target, success: true }; // Return the updated target with success flag
          } else {
            dispatch({ type: SET_ERROR, error: response.errors[0].message });
            return { ...target, success: false }; // Return the target with success flag set to false
          }
        }
      });

      const updatedTargetsResolved = await Promise.all(updatedTargets);

      const successfulTargets = updatedTargetsResolved.filter(
        (target) => target.success
      );
      const failedTargets = updatedTargetsResolved.filter(
        (target) => !target.success
      );

      if (successfulTargets.length > 0) {
        enqueueSnackbar(
          `${successfulTargets.length} target(s) updated successfully`,
          {
            anchorOrigin: {
              horizontal: 'right',
              vertical: 'top'
            },
            variant: 'success'
          }
        );
      }

      if (failedTargets.length > 0) {
        enqueueSnackbar(`${failedTargets.length} target(s) failed to update`, {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'error'
        });
      }
    } catch (err) {
      console.error(err);
      dispatch({ type: SET_ERROR, error: err.message });
    }
  }
  return (
    <>
      {Array.isArray(targets) && targets.length > 0 ? (
        <Box>
          <Scrollbar>
            <Box sx={{ minWidth: 900 }}>
              <DataGrid
                autoHeight
                rows={targets}
                getRowId={(node) => node.targetUri}
                rowHeight={80}
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
                    headerName: 'Target Type',
                    flex: 1.5,
                    editable: false
                  },
                  {
                    field: 'label',
                    headerName: 'Label',
                    flex: 2,
                    editable: true,
                    renderCell: (params) =>
                      params.value === undefined ? (
                        <CircularProgress color="primary" />
                      ) : params.value === 'NotEnoughData' ? (
                        <Chip label={params.value} color="error" />
                      ) : (
                        <div style={{ whiteSpace: 'pre-wrap', padding: '8px' }}>
                          {params.value}
                        </div>
                      )
                  },
                  {
                    field: 'description',
                    headerName: 'Description',
                    flex: 3,
                    editable: true,
                    renderCell: (params) =>
                      params.value === undefined ? (
                        <CircularProgress color="primary" />
                      ) : params.value === 'NotEnoughData' ? (
                        <Chip label={params.value} color="error" />
                      ) : (
                        <div style={{ whiteSpace: 'pre-wrap', padding: '8px' }}>
                          {params.value}
                        </div>
                      )
                  },
                  {
                    field: 'tags',
                    headerName: 'Tags',
                    flex: 2,
                    editable: true,
                    renderCell: (params) =>
                      params.value === undefined ? (
                        <CircularProgress color="primary" />
                      ) : params.value[0] === 'NotEnoughData' ? (
                        <Chip label={params.value} color="error" />
                      ) : (
                        <div style={{ whiteSpace: 'pre-wrap', padding: '8px' }}>
                          {params?.value ? params.value.join() : ''}
                        </div>
                      )
                  },
                  {
                    field: 'topics',
                    headerName: 'Topics',
                    flex: 2,
                    editable: true,
                    renderCell: (params) =>
                      params.value === undefined ? (
                        <CircularProgress color="primary" />
                      ) : params.value[0] === 'NotEnoughData' ? (
                        <Chip label={params.value} color="error" />
                      ) : (
                        <div style={{ whiteSpace: 'pre-wrap', padding: '8px' }}>
                          {params.value}
                        </div>
                      )
                  },
                  {
                    field: 'regenerate',
                    headerName: 'Regenerate',
                    flex: 3,
                    type: 'boolean',
                    renderCell: (params) =>
                      params.row.targetType === 'Table' ? (
                        <Button
                          color="primary"
                          size="small"
                          startIcon={<AutoModeIcon size={15} />}
                          sx={{ m: 4 }}
                          onClick={() => handleRegenerate(params.row)}
                          type="button"
                          variant="outlined"
                        >
                          Read Sample Data
                        </Button>
                      ) : (
                        '-'
                      )
                  }
                ]}
                columnVisibilityModel={{
                  targetUri: false,
                  label: selectedMetadataTypes['label']
                    ? selectedMetadataTypes['label']
                    : false,
                  description: selectedMetadataTypes['description']
                    ? selectedMetadataTypes['description']
                    : false,
                  tags: selectedMetadataTypes['tags']
                    ? selectedMetadataTypes['tags']
                    : false,
                  topics: selectedMetadataTypes['topics']
                    ? selectedMetadataTypes['topics']
                    : false
                }}
                pageSize={10}
                rowsPerPageOptions={[5, 10, 20]}
                pagination
                disableSelectionOnClick
                onCellEditCommit={(params) => {
                  const { value, id, field } = params;
                  const updatedTargets = targets.map((target) => {
                    const newTarget = { ...target };
                    if (newTarget.targetUri === id) {
                      newTarget[field] = value;
                    }
                    return newTarget;
                  });
                  setTargets(updatedTargets);
                }}
                onProcessRowUpdateError={(error) => {
                  console.error('Error updating row:', error);
                }}
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
        </Box>
      ) : (
        <Typography variant="body1">No metadata available</Typography>
      )}
      <Button
        color="primary"
        size="small"
        //startIcon={<AutoModeIcon size={15} />}
        sx={{ m: 2 }}
        onClick={() => saveMetadata(targets)}
        type="button"
        variant="contained"
      >
        Save
      </Button>
      <SampleDataPopup
        open={popupOpen}
        sampleData={sampleData}
        handleClose={closePopup}
        handleRegenerate={handleAcceptAndRegenerate}
      />
    </>
  );
};

ReviewMetadataComponent.propTypes = {
  dataset: PropTypes.object.isRequired,
  targetType: PropTypes.string.isRequired,
  targets: PropTypes.array.isRequired,
  setTargets: PropTypes.func.isRequired,
  selectedMetadataTypes: PropTypes.object.isRequired,
  version: PropTypes.number.isRequired,
  setVersion: PropTypes.func.isRequired
};
