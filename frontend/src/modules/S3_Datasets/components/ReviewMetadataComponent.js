import React, { useState, useEffect } from 'react';
import {
  Button,
  Box,
  Chip,
  Typography,
  CircularProgress,
  Backdrop
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import AutoModeIcon from '@mui/icons-material/AutoMode';
import SaveIcon from '@mui/icons-material/Save';
import { Scrollbar } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { updateDatasetTable } from 'modules/Tables/services';
import { updateDatasetStorageLocation } from 'modules/Folders/services';
import {
  readTableSampleData,
  updateDataset,
  generateMetadataBedrock
} from '../services';
import SampleDataPopup from './SampleDataPopup';

export const ReviewMetadataComponent = (props) => {
  const { dataset, targets, setTargets, selectedMetadataTypes, onClose } =
    props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const [popupOpen, setPopupOpen] = useState(false);
  const [sampleData, setSampleData] = useState(null);
  const [targetUri, setTargetUri] = useState(null);
  const [selectedRows, setSelectedRows] = useState([]);
  const [generatingTargets, setGeneratingTargets] = useState(new Set());
  const [loadingSampleData, setLoadingSampleData] = useState(false);

  // Check for errors in targets data when component mounts or targets change
  useEffect(() => {
    // This effect is no longer needed
  }, [targets]);

  const openSampleDataPopup = (data) => {
    setSampleData(data);
    setPopupOpen(true);
  };
  const closeSampleDataPopup = () => {
    setPopupOpen(false);
    setSampleData(null);
  };

  async function handleRegenerate(table) {
    try {
      setLoadingSampleData(true);
      const response = await client.query(
        readTableSampleData({
          tableUri: table.targetUri
        })
      );
      if (!response.errors) {
        openSampleDataPopup(response.data.readTableSampleData);
        setTargetUri(table.targetUri);
        enqueueSnackbar('Successfully read sample data', {
          variant: 'success'
        });
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (err) {
      dispatch({ type: SET_ERROR, error: err.message });
    } finally {
      setLoadingSampleData(false);
    }
  }

  async function handleRegenerateMetadata(target) {
    try {
      setGeneratingTargets((prev) => new Set([...prev, target.targetUri]));
      const response = await client.mutate(
        generateMetadataBedrock({
          resourceUri: target.targetUri,
          targetType: target.targetType,
          metadataTypes: Object.entries(selectedMetadataTypes)
            .filter(([key, value]) => value === true)
            .map(([key]) => key)
        })
      );

      if (!response.errors) {
        const targetIndex = targets.findIndex(
          (t) => t.targetUri === target.targetUri
        );
        if (targetIndex !== -1) {
          const updatedTarget = {
            ...targets[targetIndex],
            description: response.data.generateMetadata[0].description,
            label: response.data.generateMetadata[0].label,
            tags: response.data.generateMetadata[0].tags,
            topics: response.data.generateMetadata[0].topics
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
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (err) {
      dispatch({ type: SET_ERROR, error: err.message });
    } finally {
      setGeneratingTargets((prev) => {
        const newSet = new Set(prev);
        newSet.delete(target.targetUri);
        return newSet;
      });
    }
  }
  const handleAcceptAndRegenerate = async () => {
    try {
      const target = targets.find((t) => t.targetUri === targetUri);
      if (!target) {
        console.error(`Target with targetUri ${targetUri} not found`);
        enqueueSnackbar(`Metadata generation is unsuccessful`, {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'error'
        });
        return;
      }
      const { __typename, ...sampleDataWithoutTypename } = sampleData;
      const response = await client.mutate(
        generateMetadataBedrock({
          resourceUri: target.targetUri,
          targetType: target.targetType,
          metadataTypes: Object.entries(selectedMetadataTypes)
            .filter(([key, value]) => value === true)
            .map(([key]) => key),
          tableSampleData: sampleDataWithoutTypename
        })
      );

      if (!response.errors) {
        const targetIndex = targets.findIndex((t) => t.targetUri === targetUri);
        if (targetIndex !== -1) {
          const updatedTarget = {
            ...targets[targetIndex],
            description: response.data.generateMetadata[0].description,
            label: response.data.generateMetadata[0].label,
            tags: response.data.generateMetadata[0].tags,
            topics: response.data.generateMetadata[0].topics
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
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }

      closeSampleDataPopup();
    } catch (err) {
      dispatch({ type: SET_ERROR, error: err.message });
    }
  };

  async function saveMetadata(targets) {
    try {
      const updatedTargets = targets.map(async (target) => {
        const updatedMetadata = {};

        Object.entries(selectedMetadataTypes).forEach(
          ([metadataType, checked]) => {
            if (checked) {
              updatedMetadata[metadataType] = target[metadataType];
            }
          }
        );
        if (target.targetType === 'S3_Dataset') {
          updatedMetadata.KmsAlias = dataset.restricted.KmsAlias;
          const response = await client.mutate(
            updateDataset({
              datasetUri: target.targetUri,
              input: updatedMetadata
            })
          );

          if (!response.errors) {
            return { ...target, success: true };
          } else {
            dispatch({ type: SET_ERROR, error: response.errors[0].message });
            return { ...target, success: false };
          }
        } else if (target.targetType === 'Table') {
          const response = await client.mutate(
            updateDatasetTable({
              tableUri: target.targetUri,
              input: updatedMetadata
            })
          );

          if (!response.errors) {
            return { ...target, success: true };
          } else {
            dispatch({ type: SET_ERROR, error: response.errors[0].message });
            return { ...target, success: false };
          }
        } else if (target.targetType === 'Folder') {
          const response = await client.mutate(
            updateDatasetStorageLocation({
              locationUri: target.targetUri,
              input: updatedMetadata
            })
          );

          if (!response.errors) {
            return { ...target, success: true };
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

        // Close the modal when any update is successful
        if (onClose) {
          onClose();
        }
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
        <Box sx={{ margin: 2 }}>
          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              color="primary"
              size="small"
              onClick={() =>
                saveMetadata(
                  selectedRows.map((id) =>
                    targets.find((t) => t.targetUri === id)
                  )
                )
              }
              type="button"
              variant="contained"
              disabled={selectedRows.length === 0}
              startIcon={<SaveIcon />}
            >
              Save Selected ({selectedRows.length})
            </Button>
          </Box>
          <Scrollbar>
            <Box sx={{ minWidth: 900, padding: 2 }}>
              <DataGrid
                autoHeight
                rows={targets}
                getRowId={(node) => node.targetUri}
                getRowHeight={() => 'auto'}
                getEstimatedRowHeight={() => 100}
                checkboxSelection
                onSelectionModelChange={(newSelectionModel) => {
                  setSelectedRows(newSelectionModel);
                }}
                selectionModel={selectedRows}
                isRowSelectable={(params) => {
                  const metadataFields = [
                    'label',
                    'description',
                    'tags',
                    'topics'
                  ];
                  return !metadataFields.some((field) => {
                    const value = params.row[field];
                    return (
                      value === 'Error' ||
                      value === 'NotEnoughData' ||
                      (Array.isArray(value) && value.includes('Error')) ||
                      (Array.isArray(value) && value.includes('NotEnoughData'))
                    );
                  });
                }}
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
                      generatingTargets.has(params.row.targetUri) ? (
                        <CircularProgress color="primary" size={20} />
                      ) : params.value === 'NotEnoughData' ? (
                        <Chip label={params.value} color="warning" />
                      ) : params.value === 'Error' ? (
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
                      generatingTargets.has(params.row.targetUri) ? (
                        <CircularProgress color="primary" size={20} />
                      ) : params.value === 'NotEnoughData' ? (
                        <Chip label={params.value} color="warning" />
                      ) : params.value === 'Error' ? (
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
                    valueSetter: (params) => {
                      const { row, newValue } = params;
                      const tags =
                        typeof newValue === 'string'
                          ? newValue.split(',')
                          : newValue;
                      return { ...row, tags };
                    },
                    renderCell: (params) =>
                      generatingTargets.has(params.row.targetUri) ? (
                        <CircularProgress color="primary" size={20} />
                      ) : params.value === 'NotEnoughData' ||
                        (Array.isArray(params.value) &&
                          params.value.includes('NotEnoughData')) ? (
                        <Chip
                          label={
                            Array.isArray(params.value)
                              ? 'NotEnoughData'
                              : params.value
                          }
                          color="warning"
                        />
                      ) : params.value === 'Error' ||
                        (Array.isArray(params.value) &&
                          params.value.includes('Error')) ? (
                        <Chip
                          label={
                            Array.isArray(params.value) ? 'Error' : params.value
                          }
                          color="error"
                        />
                      ) : (
                        <div style={{ whiteSpace: 'pre-wrap', padding: '8px' }}>
                          {Array.isArray(params.value)
                            ? params.value.join(', ')
                            : params.value}
                        </div>
                      )
                  },
                  {
                    field: 'topics',
                    headerName: 'Topics',
                    flex: 2,
                    editable: true,
                    renderCell: (params) =>
                      generatingTargets.has(params.row.targetUri) ? (
                        <CircularProgress color="primary" size={20} />
                      ) : params.value === 'NotEnoughData' ? (
                        <Chip label={params.value} color="warning" />
                      ) : params.value === 'Error' ? (
                        <Chip label={params.value} color="error" />
                      ) : (
                        <div style={{ whiteSpace: 'pre-wrap', padding: '8px' }}>
                          {params.value}
                        </div>
                      )
                  },
                  {
                    field: 'actions',
                    headerName: 'Actions',
                    flex: 4,
                    minWidth: 300,
                    type: 'boolean',
                    renderCell: (params) => (
                      <Box
                        sx={{
                          display: 'flex',
                          gap: 1,
                          flexDirection: 'column',
                          width: '100%'
                        }}
                      >
                        <Button
                          color="secondary"
                          size="small"
                          fullWidth
                          startIcon={
                            generatingTargets.has(params.row.targetUri) ? (
                              <CircularProgress size={16} color="inherit" />
                            ) : (
                              <AutoModeIcon size={15} />
                            )
                          }
                          onClick={() => handleRegenerateMetadata(params.row)}
                          type="button"
                          variant="outlined"
                          disabled={generatingTargets.has(params.row.targetUri)}
                        >
                          {generatingTargets.has(params.row.targetUri)
                            ? 'Generating...'
                            : 'Regenerate'}
                        </Button>
                        {params.row.targetType === 'Table' && (
                          <Button
                            color="primary"
                            size="small"
                            fullWidth
                            startIcon={
                              loadingSampleData ? (
                                <CircularProgress size={16} color="inherit" />
                              ) : (
                                <AutoModeIcon size={15} />
                              )
                            }
                            onClick={() => handleRegenerate(params.row)}
                            type="button"
                            variant="outlined"
                            disabled={loadingSampleData}
                          >
                            {loadingSampleData
                              ? 'Loading...'
                              : 'Read Sample Data'}
                          </Button>
                        )}
                      </Box>
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
                    borderBottom: 0.5,
                    padding: '0 8px'
                  },
                  '& .MuiDataGrid-cell': {
                    whiteSpace: 'normal !important',
                    wordBreak: 'break-word',
                    padding: '16px 8px',
                    lineHeight: 1.5
                  },
                  '& .MuiDataGrid-main': {
                    margin: '0 8px'
                  }
                }}
              />
            </Box>
          </Scrollbar>
        </Box>
      ) : (
        <Typography variant="body1">No metadata available</Typography>
      )}

      {loadingSampleData && (
        <Backdrop
          sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}
          open={loadingSampleData}
        >
          <CircularProgress color="inherit" size={60} />
        </Backdrop>
      )}

      <SampleDataPopup
        open={popupOpen}
        sampleData={sampleData}
        handleClose={closeSampleDataPopup}
        handleRegenerate={handleAcceptAndRegenerate}
      />
    </>
  );
};

ReviewMetadataComponent.propTypes = {
  dataset: PropTypes.object.isRequired,
  targets: PropTypes.array.isRequired,
  setTargets: PropTypes.func.isRequired,
  selectedMetadataTypes: PropTypes.object.isRequired
};
