import PropTypes from 'prop-types';
import { Box, Card, CardContent, CardHeader, Divider, Grid, Typography } from '@mui/material';
import { deleteMetadataFormVersion, listMetadataFormVersions } from '../services';
import { SET_ERROR } from '../../../globalErrors';
import React, { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import { useClient } from '../../../services';
import DeleteIcon from '@mui/icons-material/DeleteOutlined';
import DoNotDisturbAltOutlinedIcon from '@mui/icons-material/DoNotDisturbAltOutlined';
import { useSnackbar } from 'notistack';

export const MetadataFormAttachedEntities = (props) => {
  const { metadataForm, userRolesMF } = props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const [versions, setVersions] = useState([]);
  const [selectedVersion, setSelectedVersion] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchVersions = async () => {
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
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Versions not found';
      dispatch({ type: SET_ERROR, error });
    }
  };

  useEffect(() => {
    if (client) {
      fetchVersions().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch]);

  const deleteVersion = async (version) => {
    setLoading(true);
    const response = await client.mutate(
      deleteMetadataFormVersion(version.metadataFormUri, version.version)
    );
    if (
      !response.errors &&
      response.data &&
      response.data.deleteMetadataFormVersion !== null
    ) {
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
  const fetchAttachedEntities = async (version) => {};

  return (
    <Box >
      <Grid container spacing={2} sx={{ height: 'calc(100vh - 320px)', mb: -5 }}>
        <Grid item lg={2} xl={2}>
          <Card sx={{ height: '100%' }}>
            <CardHeader title='Versions'/>

            <Divider/>
            {versions.length > 0 ? (
              versions.map((version) => (
                <CardContent
                  sx={{
                    backgroundColor:
                      selectedVersion &&
                      selectedVersion.version === version.version
                        ? '#e6e6e6'
                        : 'white'
                  }}
                >
                  <Grid container spacing={2}>
                    <Grid
                      item
                      lg={7}
                      xl={7}
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
                        {' version ' + version.version }
                      </Typography>
                    </Grid>
                    <Grid item lg={3} xl={3}>
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
                        { version.attached_forms}
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
                        onClick={() => deleteVersion(version)}
                      />
                        )}
                    </Grid>
                  </Grid>
                </CardContent>
              ))
            ) : (
              <CardContent sx={{ display: 'flex', justifyContent: 'center' }}>
                <DoNotDisturbAltOutlinedIcon sx={{ mr: 1 }} />
                <Typography variant="subtitle2" color="textPrimary">
                  No Metadata Forms Attached
                </Typography>
              </CardContent>
            )}
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

MetadataFormAttachedEntities.propTypes = {
  metadataForm: PropTypes.any.isRequired
};
