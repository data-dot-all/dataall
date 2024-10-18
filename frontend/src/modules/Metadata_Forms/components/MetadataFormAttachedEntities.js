import PropTypes from 'prop-types';
import { Box, Card, CardContent, Grid, Typography } from '@mui/material';
import { listMetadataFormVersions } from '../services';
import { SET_ERROR } from '../../../globalErrors';
import React, { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import { useClient } from '../../../services';
import DeleteIcon from '@mui/icons-material/DeleteOutlined';
import DoNotDisturbAltOutlinedIcon from '@mui/icons-material/DoNotDisturbAltOutlined';

export const MetadataFormAttachedEntities = (props) => {
  const { metadataForm } = props;
  const dispatch = useDispatch();
  const client = useClient();
  const [versions, setVersions] = useState([]);
  const [selectedVersion, setSelectedVersion] = useState(null);

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

  const deleteVersion = async (version) => {};

  const fetchAttachedEntities = async (version) => {};

  return (
    <Box >
      <Grid container spacing={2} sx={{ height: 'calc(100vh - 320px)', mb: -5 }}>
        <Grid item lg={2} xl={2}>
          <Card sx={{ height: '100%' }}>
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
                      lg={10}
                      xl={10}
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

                    <Grid item lg={2} xl={2}>
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
