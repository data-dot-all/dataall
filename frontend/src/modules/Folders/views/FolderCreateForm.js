import { LoadingButton } from '@mui/lab';
import {
  Box,
  Breadcrumbs,
  Button,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  Container,
  FormHelperText,
  Grid,
  Link,
  TextField,
  Typography
} from '@mui/material';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom';
import * as Yup from 'yup';
import {
  ArrowLeftIcon,
  ChevronRightIcon,
  ChipInput,
  useSettings
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient, addDatasetStorageLocation, getDataset } from 'services';

function FolderCreateHeader(props) {
  const { dataset } = props;
  return (
    <Grid container justifyContent="space-between" spacing={3}>
      <Grid item>
        <Typography color="textPrimary" variant="h5">
          Create a new folder
        </Typography>
        <Breadcrumbs
          aria-label="breadcrumb"
          separator={<ChevronRightIcon fontSize="small" />}
          sx={{ mt: 1 }}
        >
          <Link underline="hover" color="textPrimary" variant="subtitle2">
            Discover
          </Link>
          <Link
            underline="hover"
            color="textPrimary"
            component={RouterLink}
            to="/console/datasets"
            variant="subtitle2"
          >
            Datasets
          </Link>
          <Link
            underline="hover"
            color="textPrimary"
            component={RouterLink}
            to={`/console/s3-datasets/${dataset.datasetUri}`}
            variant="subtitle2"
          >
            {dataset.name}
          </Link>
        </Breadcrumbs>
      </Grid>
      <Grid item>
        <Box sx={{ m: -1 }}>
          <Button
            color="primary"
            component={RouterLink}
            startIcon={<ArrowLeftIcon fontSize="small" />}
            sx={{ mt: 1 }}
            to={`/console/s3-datasets/${dataset.datasetUri}`}
            variant="outlined"
          >
            Cancel
          </Button>
        </Box>
      </Grid>
    </Grid>
  );
}

FolderCreateHeader.propTypes = { dataset: PropTypes.object.isRequired };

const FolderCreateForm = () => {
  const params = useParams();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const client = useClient();
  const { settings } = useSettings();
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = useState(true);
  const [dataset, setDataset] = useState(null);

  const fetchItem = useCallback(async () => {
    setLoading(true);
    const response = await client.query(getDataset(params.uri));
    if (!response.errors && response.data.getDataset !== null) {
      setDataset(response.data.getDataset);
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Dataset not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  }, [client, dispatch, params.uri]);
  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, fetchItem, dispatch]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        addDatasetStorageLocation({
          datasetUri: dataset.datasetUri,
          input: {
            label: values.label,
            prefix: values.prefix,
            tags: values.tags,
            description: values.description
          }
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Folder creation started', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        navigate(
          `/console/s3-datasets/folder/${response.data.createDatasetStorageLocation.locationUri}`
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (err) {
      console.error(err);
      setStatus({ success: false });
      setErrors({ submit: err.message });
      setSubmitting(false);
      dispatch({ type: SET_ERROR, error: err.message });
    }
  }
  if (loading) {
    return <CircularProgress />;
  }
  if (!dataset) {
    return null;
  }

  return (
    <>
      <Helmet>
        <title>Folders: Folder Create | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 8
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <FolderCreateHeader dataset={dataset} />
          <Box sx={{ mt: 3 }}>
            <Formik
              initialValues={{
                label: '',
                prefix: '',
                description: '',
                tags: []
              }}
              validationSchema={Yup.object().shape({
                label: Yup.string()
                  .max(255)
                  .required('*Folder name is required'),
                prefix: Yup.string().max(255).required('*Prefix is required'),
                description: Yup.string().max(5000),
                tags: Yup.array().min(1).required('*Tags are required')
              })}
              onSubmit={async (
                values,
                { setErrors, setStatus, setSubmitting }
              ) => {
                await submit(values, setStatus, setSubmitting, setErrors);
              }}
            >
              {({
                errors,
                handleBlur,
                handleChange,
                handleSubmit,
                isSubmitting,
                setFieldValue,
                touched,
                values
              }) => (
                <form onSubmit={handleSubmit}>
                  <Grid container spacing={3}>
                    <Grid item lg={8} md={6} xs={12}>
                      <Card>
                        <CardHeader title="Details" />
                        <CardContent>
                          <TextField
                            error={Boolean(touched.label && errors.label)}
                            fullWidth
                            helperText={touched.label && errors.label}
                            label="Folder name"
                            name="label"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.label}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            error={Boolean(touched.prefix && errors.prefix)}
                            fullWidth
                            helperText={touched.prefix && errors.prefix}
                            label="Amazon S3 prefix"
                            name="prefix"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.prefix}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            FormHelperTextProps={{
                              sx: {
                                textAlign: 'right',
                                mr: 0
                              }
                            }}
                            fullWidth
                            helperText={`${
                              200 - values.description.length
                            } characters left`}
                            label="Short description"
                            name="description"
                            multiline
                            onBlur={handleBlur}
                            onChange={handleChange}
                            rows={5}
                            value={values.description}
                            variant="outlined"
                          />
                          {touched.description && errors.description && (
                            <Box sx={{ mt: 2 }}>
                              <FormHelperText error>
                                {errors.description}
                              </FormHelperText>
                            </Box>
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item lg={4} md={6} xs={12}>
                      <Card>
                        <CardHeader title="Organize" />
                        <CardContent>
                          <ChipInput
                            error={Boolean(touched.tags && errors.tags)}
                            fullWidth
                            placeholder="Hit enter after typing value"
                            helperText={touched.tags && errors.tags}
                            variant="outlined"
                            label="Tags"
                            onChange={(chip) => {
                              setFieldValue('tags', [...chip]);
                            }}
                          />
                        </CardContent>
                      </Card>
                      {errors.submit && (
                        <Box sx={{ mt: 3 }}>
                          <FormHelperText error>{errors.submit}</FormHelperText>
                        </Box>
                      )}
                      <Box
                        sx={{
                          display: 'flex',
                          justifyContent: 'flex-end',
                          mt: 3
                        }}
                      >
                        <LoadingButton
                          color="primary"
                          disabled={isSubmitting}
                          type="submit"
                          variant="contained"
                        >
                          Create folder
                        </LoadingButton>
                      </Box>
                    </Grid>
                  </Grid>
                </form>
              )}
            </Formik>
          </Box>
        </Container>
      </Box>
    </>
  );
};

export default FolderCreateForm;
