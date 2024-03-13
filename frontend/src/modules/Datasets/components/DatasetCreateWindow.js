import { CloudDownloadOutlined } from '@mui/icons-material';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Dialog,
  Grid,
  Typography
} from '@mui/material';
import PropTypes from 'prop-types';
import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { PlusIcon } from '../../../design';
import { isModuleEnabled, ModuleNames } from 'utils';

export const DatasetCreateWindow = (props) => {
  const { onClose, open, ...other } = props;

  return (
    <Dialog maxWidth="lg" fullWidth onClose={onClose} open={open} {...other}>
      <Box sx={{ mt: 3 }}>
        <Grid container spacing={1} alignItems="center">
          {isModuleEnabled(ModuleNames.DATASETS) && (
            <Grid item justifyContent="center" md={3} lg={3} xl={3}>
              <Card>
                <CardHeader title="Create S3/Glue Dataset" />
                <CardContent>
                  <Typography
                    color="textSecondary"
                    gutterBottom
                    variant="subtitle2"
                  >
                    Data.all will create an S3 Bucket encrypted with KMS key and
                    a Glue database
                  </Typography>
                  <Button
                    color="primary"
                    component={RouterLink}
                    startIcon={<PlusIcon fontSize="small" />}
                    sx={{ m: 1 }}
                    to="/console/datasets/new"
                    variant="contained"
                  >
                    Create
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          )}
          {isModuleEnabled(ModuleNames.DATASETS) && (
            <Grid item justifyContent="center" md={3} lg={3} xl={3}>
              <Card>
                <CardHeader title="Import S3/Glue Dataset" />
                <CardContent>
                  <Typography
                    color="textSecondary"
                    gutterBottom
                    variant="subtitle2"
                  >
                    Data.all will use the S3 Bucket as it is encrypted and will
                    create a Glue database if you do not provide one
                  </Typography>
                  <Button
                    color="primary"
                    component={RouterLink}
                    startIcon={<CloudDownloadOutlined fontSize="small" />}
                    sx={{ m: 1 }}
                    to="/console/datasets/import"
                    variant="outlined"
                  >
                    Import
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          )}
          {isModuleEnabled(ModuleNames.WAREHOUSES) && (
            <Grid item justifyContent="center" md={3} lg={3} xl={3}>
              <Card>
                <CardHeader title="Import Redshift Dataset" />
                <CardContent>
                  <Typography
                    color="textSecondary"
                    gutterBottom
                    variant="subtitle2"
                  >
                    Data.all will import the metadata of an existing Redshift
                    database using a Warehouse Connection
                  </Typography>
                  <Button
                    color="primary"
                    component={RouterLink}
                    startIcon={<CloudDownloadOutlined fontSize="small" />}
                    sx={{ m: 1 }}
                    to="/console/warehouseDatasets/import"
                    variant="outlined"
                  >
                    Import
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      </Box>
    </Dialog>
  );
};

DatasetCreateWindow.propTypes = {
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired
  //reloadRoles: PropTypes.func
};
