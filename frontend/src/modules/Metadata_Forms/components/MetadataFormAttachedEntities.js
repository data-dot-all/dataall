import PropTypes from 'prop-types';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Grid,
  Typography
} from '@mui/material';
import {
  deleteMetadataFormVersion,
  getAttachedMetadataForm,
  listAttachedMetadataForms,
  listMetadataFormVersions
} from '../services';
import { SET_ERROR } from 'globalErrors';
import React, { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import { useClient } from 'services';
import DeleteIcon from '@mui/icons-material/DeleteOutlined';
import DoNotDisturbAltOutlinedIcon from '@mui/icons-material/DoNotDisturbAltOutlined';
import { useSnackbar } from 'notistack';
import { DataGrid } from '@mui/x-data-grid';
import { AttachedFormCard } from './AttachedFormCard';
import CircularProgress from '@mui/material/CircularProgress';
import { useTheme } from '@mui/styles';
import { DeleteObjectWithFrictionModal } from 'design';

export const MetadataFormAttachedEntities = (props) => {
  const { metadataForm, userRolesMF } = props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const theme = useTheme();
  const [versions, setVersions] = useState([]);
  const [selectedVersion, setSelectedVersion] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingVersions, setLoadingVersions] = useState(true);
  const [loadingForm, setLoadingForm] = useState(true);
  const [attachedEntities, setAttachedEntities] = useState({});
  const [attachedForm, setAttachedForm] = useState(null);
  const [paginationModel, setPaginationModel] = useState({
    pageSize: 10,
    page: 0
  });
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [isDeleteRoleModalOpen, setIsDeleteRoleModalOpen] = useState(false);

  const header = [
    { field: 'entityType', width: 200, headerName: 'Type', editable: false },
    { field: 'entityName', width: 200, headerName: 'Name', editable: false },
    { field: 'entityOwner', width: 200, headerName: 'Owner', editable: false }
  ];

  const handleDeleteRoleModalOpen = (uri) => {
    setIsDeleteRoleModalOpen(true);
    setSelectedVersion(uri);
  };
  const handleDeleteRoleModalClosed = () => {
    setIsDeleteRoleModalOpen(false);
    setSelectedVersion(null);
  };

  const fetchVersions = async () => {
    setLoadingVersions(true);
    const response = await client.query(
      listMetadataFormVersions(metadataForm.uri)
    );
    if (
      !response.errors &&
      response.data &&
      response.data.listMetadataFormVersions !== null
    ) {
      setVersions(response.data.listMetadataFormVersions);
      setSelectedVersion(response.data.listMetadataFormVersions[0]);
      await fetchAttachedEntities(response.data.listMetadataFormVersions[0]);
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Versions not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoadingVersions(false);
  };

  const fetchAttachedForm = async (uri) => {
    setLoadingForm(true);
    const response = await client.query(getAttachedMetadataForm(uri));
    if (
      !response.errors &&
      response.data &&
      response.data.getAttachedMetadataForm !== null
    ) {
      setAttachedForm(response.data.getAttachedMetadataForm);
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Attached Metadata Form not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoadingForm(false);
  };

  useEffect(() => {
    if (client) {
      fetchVersions().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch]);

  const deleteVersion = async () => {
    const version = selectedVersion;
    setLoading(true);
    const response = await client.mutate(
      deleteMetadataFormVersion(version.metadataFormUri, version.version)
    );
    if (
      !response.errors &&
      response.data &&
      response.data.deleteMetadataFormVersion !== null
    ) {
      handleDeleteRoleModalClosed();
      await fetchVersions();
      enqueueSnackbar('Version deleted', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Delete version failed';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  };
  const fetchAttachedEntities = async (
    version,
    page = paginationModel.page,
    pageSize = paginationModel.pageSize
  ) => {
    setLoading(true);

    const response = await client.query(
      listAttachedMetadataForms({
        pageSize: pageSize,
        page: page + 1,
        metadataFormUri: version.metadataFormUri,
        version: version.version
      })
    );
    if (
      !response.errors &&
      response.data &&
      response.data.listAttachedMetadataForms !== null
    ) {
      response.data.listAttachedMetadataForms.nodes =
        response.data.listAttachedMetadataForms.nodes.map((entity) => ({
          id: entity.uri,
          ...entity
        }));
      setAttachedEntities(response.data.listAttachedMetadataForms);
      if (response.data.listAttachedMetadataForms.nodes.length > 0) {
        setSelectedEntity([
          response.data.listAttachedMetadataForms.nodes[0].uri
        ]);
        await fetchAttachedForm(
          response.data.listAttachedMetadataForms.nodes[0].uri
        );
      } else {
        setAttachedForm(null);
      }
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Attached entities not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  };

  return (
    <Box>
      <Grid
        container
        spacing={2}
        sx={{ height: 'calc(100vh - 320px)', mb: -5 }}
      >
        <Grid item lg={2} xl={2}>
          <Card sx={{ height: '100%' }}>
            <CardHeader title="Versions" />

            <Divider />
            {versions.length > 0 && !loadingVersions ? (
              versions.map((version) => (
                <CardContent
                  sx={{
                    backgroundColor:
                      selectedVersion &&
                      selectedVersion.version === version.version &&
                      theme.palette.action.selected
                  }}
                >
                  <Grid container spacing={2}>
                    <Grid
                      item
                      lg={5}
                      xl={5}
                      onClick={async () => {
                        setSelectedVersion(version);
                        await fetchAttachedEntities(version);
                      }}
                    >
                      <Typography
                        color="textPrimary"
                        variant="subtitle2"
                        sx={{
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          maxLines: 1
                        }}
                      >
                        {' version ' + version.version}
                      </Typography>
                    </Grid>
                    <Grid item lg={5} xl={5}>
                      <Typography
                        color="textPrimary"
                        onClick={async () => {
                          setSelectedVersion(version);
                          await fetchAttachedEntities(version);
                        }}
                        variant="subtitle2"
                        sx={{
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          maxLines: 1
                        }}
                      >
                        {'Count: ' + version.attached_forms}
                      </Typography>
                    </Grid>
                    <Grid item lg={2} xl={2}>
                      {metadataForm.userRole === userRolesMF.Owner && (
                        <DeleteIcon
                          sx={{ color: 'primary.main', opacity: 0.5 }}
                          onMouseOver={(e) => {
                            e.currentTarget.style.opacity = 1;
                          }}
                          onMouseOut={(e) => {
                            e.currentTarget.style.opacity = 0.5;
                          }}
                          onClick={() => handleDeleteRoleModalOpen(version)}
                        />
                      )}
                    </Grid>
                  </Grid>
                </CardContent>
              ))
            ) : (
              <CardContent sx={{ display: 'flex', justifyContent: 'center' }}>
                {!loadingVersions && (
                  <>
                    <DoNotDisturbAltOutlinedIcon sx={{ mr: 1 }} />
                    <Typography variant="subtitle2" color="textPrimary">
                      No Metadata Form Versions
                    </Typography>
                  </>
                )}
              </CardContent>
            )}
            {loadingVersions && (
              <CardContent sx={{ display: 'flex', justifyContent: 'center' }}>
                <CircularProgress />
              </CardContent>
            )}
          </Card>
        </Grid>
        <Grid item lg={5} xl={5}>
          <Card sx={{ height: '100%' }}>
            <CardHeader title="Attached Entities" />
            <CardContent>
              {!loading &&
              attachedEntities.nodes &&
              attachedEntities.nodes.length > 0 ? (
                <DataGrid
                  rows={attachedEntities.nodes}
                  columns={header}
                  pageSize={paginationModel.pageSize}
                  rowsPerPageOptions={[5, 10, 20]}
                  onPageSizeChange={async (newPageSize) => {
                    setPaginationModel({
                      ...paginationModel,
                      pageSize: newPageSize
                    });
                    await fetchAttachedEntities(
                      selectedVersion,
                      paginationModel.page,
                      newPageSize
                    );
                  }}
                  page={paginationModel.page}
                  onPageChange={async (newPage) => {
                    setPaginationModel({ ...paginationModel, page: newPage });
                    await fetchAttachedEntities(
                      selectedVersion,
                      newPage,
                      paginationModel.pageSize
                    );
                  }}
                  rowCount={attachedEntities.count}
                  autoHeight={true}
                  onSelectionModelChange={async (newSelection) => {
                    setSelectedEntity(newSelection);
                    if (newSelection.length > 0) {
                      await fetchAttachedForm(newSelection[0]);
                    }
                  }}
                  selectionModel={selectedEntity}
                  hideFooterSelectedRowCount={true}
                />
              ) : (
                <Typography color="textPrimary" variant="subtitle2">
                  {loading ? '' : 'No entities attached.'}
                </Typography>
              )}
              {loading && (
                <CardContent sx={{ display: 'flex', justifyContent: 'center' }}>
                  <CircularProgress />
                </CardContent>
              )}
            </CardContent>
          </Card>
        </Grid>
        <Grid item lg={5} xl={5}>
          {!loadingForm && !loading && selectedEntity && attachedForm && (
            <AttachedFormCard
              attachedForm={attachedForm}
              fields={attachedForm.fields}
              editable={false}
            />
          )}
          {loadingForm ||
            (loading && (
              <CardContent sx={{ display: 'flex', justifyContent: 'center' }}>
                <CircularProgress />
              </CardContent>
            ))}
        </Grid>
      </Grid>
      <div>
        <DeleteObjectWithFrictionModal
          objectName={metadataForm.name}
          onApply={handleDeleteRoleModalClosed}
          onClose={handleDeleteRoleModalClosed}
          deleteMessage={
            <>
              <Typography align={'center'} variant="subtitle2" color="error">
                Are you sure you want to delete this version of metadata form ?{' '}
              </Typography>
            </>
          }
          open={isDeleteRoleModalOpen}
          isAWSResource={false}
          deleteFunction={deleteVersion}
        />
      </div>
    </Box>
  );
};

MetadataFormAttachedEntities.propTypes = {
  metadataForm: PropTypes.any.isRequired
};
