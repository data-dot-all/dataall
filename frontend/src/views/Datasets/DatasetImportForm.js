import React, { useCallback, useEffect, useState } from 'react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import * as Yup from 'yup';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import {
  Autocomplete,
  Box,
  Breadcrumbs,
  Button,
  Card,
  CardContent,
  CardHeader,
  Chip,
  CircularProgress,
  Container,
  FormHelperText,
  Grid,
  Link,
  MenuItem,
  TextField,
  Typography
} from '@mui/material';
import { Helmet } from 'react-helmet-async';
import { LoadingButton } from '@mui/lab';
import useClient from '../../hooks/useClient';
import ChevronRightIcon from '../../icons/ChevronRight';
import ArrowLeftIcon from '../../icons/ArrowLeft';
import useSettings from '../../hooks/useSettings';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import listEnvironments from '../../api/Environment/listEnvironments';
import ChipInput from '../../components/TagsInput';
import TopicsData from '../../components/topics/TopicsData';
import importDataset from '../../api/Dataset/importDataset';
import listEnvironmentGroups from '../../api/Environment/listEnvironmentGroups';
import * as Defaults from '../../components/defaults';
import DatasetLFTagsForm from './DatasetLFTagsForm';

const DatasetImportForm = (props) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const client = useClient();
  const { settings } = useSettings();
  const [loading, setLoading] = useState(true);
  const [groupOptions, setGroupOptions] = useState([]);
  const [datasetLFTags, setDatasetLFTags] = useState([]);
  const [environmentOptions, setEnvironmentOptions] = useState([]);
  const [confidentialityOptions] = useState([
    'Unclassified',
    'Official',
    'Secret'
  ]);

  // const handleDatasetLFTags = tags => {
  //   setDatasetLFTags(tags);
  // };

  const fetchEnvironments = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      listEnvironments({
        filter: Defaults.SelectListFilter
      })
    );
    if (!response.errors) {
      setEnvironmentOptions(
        response.data.listEnvironments.nodes.map((e) => ({
          ...e,
          value: e.environmentUri,
          label: e.label
        }))
      );
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch]);
  const fetchGroups = async (environmentUri) => {
    try {
      const response = await client.query(
        listEnvironmentGroups({
          filter: Defaults.SelectListFilter,
          environmentUri
        })
      );
      if (!response.errors) {
        setGroupOptions(
          response.data.listEnvironmentGroups.nodes.map((g) => ({
            value: g.groupUri,
            label: g.groupUri
          }))
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
  };
  useEffect(() => {
    if (client) {
      fetchEnvironments().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch, fetchEnvironments]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        importDataset({
          organizationUri: values.environment.organization.organizationUri,
          environmentUri: values.environment.environmentUri,
          owner: '',
          label: values.label,
          SamlAdminGroupName: values.SamlGroupName,
          tags: values.tags,
          description: values.description,
          topics: values.topics ? values.topics.map((t) => t.value) : [],
          bucketName: values.bucketName,
          glueDatabaseName: values.glueDatabaseName,
          stewards: values.stewards,
          confidentiality: values.confidentiality,
          lfTagKey: datasetLFTags ? datasetLFTags.map((d) => d.lfTagKey) : [],
          lfTagValue: datasetLFTags ? datasetLFTags.map((d) => d.lfTagValue) : []
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Dataset imported successfully', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        navigate(`/console/datasets/${response.data.importDataset.datasetUri}`);
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

  return (
    <>
      <Helmet>
        <title>Dataset: Dataset Import | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 8
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <Grid container justifyContent="space-between" spacing={3}>
            <Grid item>
              <Typography color="textPrimary" variant="h5">
                Import a new dataset
              </Typography>
              <Breadcrumbs
                aria-label="breadcrumb"
                separator={<ChevronRightIcon fontSize="small" />}
                sx={{ mt: 1 }}
              >
                <Typography color="textPrimary" variant="subtitle2">
                  Contribute
                </Typography>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/datasets"
                  variant="subtitle2"
                >
                  Datasets
                </Link>
                <Typography color="textPrimary" variant="subtitle2">
                  Import
                </Typography>
              </Breadcrumbs>
            </Grid>
            <Grid item>
              <Box sx={{ m: -1 }}>
                <Button
                  color="primary"
                  component={RouterLink}
                  startIcon={<ArrowLeftIcon fontSize="small" />}
                  sx={{ mt: 1 }}
                  to="/console/datasets"
                  variant="outlined"
                >
                  Cancel
                </Button>
              </Box>
            </Grid>
          </Grid>
          <Box sx={{ mt: 3 }}>
            <Formik
              initialValues={{
                label: '',
                description: '',
                environment: '',
                businessOwnerEmail: '',
                businessOwnerDelegationEmails: [],
                SamlGroupName: '',
                stewards: '',
                tags: [],
                topics: [],
                glueDatabaseName: '',
                bucketName: '',
                confidentiality: ''
              }}
              validationSchema={Yup.object().shape({
                label: Yup.string()
                  .max(255)
                  .required('*Dataset name is required'),
                description: Yup.string().max(5000),
                SamlGroupName: Yup.string()
                  .max(255)
                  .required('*Team is required'),
                topics: Yup.array().min(1).required('*Topics are required'),
                environment: Yup.object().required('*Environment is required'),
                tags: Yup.array().min(1).required('*Tags are required'),
                glueDatabaseName: Yup.string().max(255),
                bucketName: Yup.string()
                  .max(255)
                  .required('*S3 bucket name is required'),
                confidentiality: Yup.string()
                  .max(255)
                  .required('*Confidentiality is required')
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
                <form onSubmit={handleSubmit} {...props}>
                  <Grid container spacing={3}>
                    <Grid item lg={7} md={7} xs={12}>
                      <Card>
                        <CardHeader title="Details" />
                        <CardContent>
                          <TextField
                            error={Boolean(touched.label && errors.label)}
                            fullWidth
                            helperText={touched.label && errors.label}
                            label="Dataset name"
                            name="label"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.label}
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
                            error={Boolean(
                              touched.description && errors.description
                            )}
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
                      <Card sx={{ mt: 3 }}>
                        <CardHeader title="Classification" />
                        <CardContent>
                          <TextField
                            fullWidth
                            error={Boolean(
                              touched.confidentiality && errors.confidentiality
                            )}
                            helperText={
                              touched.confidentiality && errors.confidentiality
                            }
                            label="Confidentiality"
                            name="confidentiality"
                            onChange={handleChange}
                            select
                            value={values.confidentiality}
                            variant="outlined"
                          >
                            {confidentialityOptions.map((c) => (
                              <MenuItem key={c} value={c}>
                                {c}
                              </MenuItem>
                            ))}
                          </TextField>
                        </CardContent>
                        <CardContent>
                          <Autocomplete
                            multiple
                            id="tags-filled"
                            options={TopicsData}
                            getOptionLabel={(opt) => opt.label}
                            onChange={(event, value) => {
                              setFieldValue('topics', value);
                            }}
                            renderTags={(tagValue, getTagProps) =>
                              tagValue.map((option, index) => (
                                <Chip
                                  label={option.label}
                                  {...getTagProps({ index })}
                                />
                              ))
                            }
                            renderInput={(p) => (
                              <TextField
                                {...p}
                                variant="outlined"
                                label="Topics"
                                error={Boolean(touched.topics && errors.topics)}
                                helperText={touched.topics && errors.topics}
                              />
                            )}
                          />
                        </CardContent>
                        <CardContent>
                          <Box>
                            <ChipInput
                              fullWidth
                              error={Boolean(touched.tags && errors.tags)}
                              helperText={touched.tags && errors.tags}
                              variant="outlined"
                              label="Tags"
                              placeholder="Hit enter after typing value"
                              onChange={(chip) => {
                                setFieldValue('tags', [...chip]);
                              }}
                            />
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item lg={5} md={5} xs={12}>
                      <Card sx={{ mb: 3 }}>
                        <CardHeader title="Deployment" />
                        <CardContent>
                          <TextField
                            fullWidth
                            error={Boolean(
                              touched.environment && errors.environment
                            )}
                            helperText={
                              touched.environment && errors.environment
                            }
                            label="Environment"
                            name="environment"
                            onChange={(event) => {
                              setFieldValue('SamlGroupName', '');
                              fetchGroups(
                                event.target.value.environmentUri
                              ).catch((e) =>
                                dispatch({ type: SET_ERROR, error: e.message })
                              );
                              setFieldValue('environment', event.target.value);
                            }}
                            select
                            value={values.environment}
                            variant="outlined"
                          >
                            {environmentOptions.map((environment) => (
                              <MenuItem
                                key={environment.environmentUri}
                                value={environment}
                              >
                                {environment.label}
                              </MenuItem>
                            ))}
                          </TextField>
                        </CardContent>
                        <CardContent>
                          <TextField
                            disabled
                            fullWidth
                            label="Region"
                            name="region"
                            value={
                              values.environment
                                ? values.environment.region
                                : ''
                            }
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            disabled
                            fullWidth
                            label="Organization"
                            name="organization"
                            value={
                              values.environment
                                ? values.environment.organization.label
                                : ''
                            }
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            error={Boolean(
                              touched.bucketName && errors.bucketName
                            )}
                            fullWidth
                            helperText={touched.bucketName && errors.bucketName}
                            label="Amazon S3 bucket name"
                            name="bucketName"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.bucketName}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            error={Boolean(
                              touched.glueDatabaseName &&
                                errors.glueDatabaseName
                            )}
                            fullWidth
                            helperText={
                              touched.glueDatabaseName &&
                              errors.glueDatabaseName
                            }
                            label="AWS Glue database name"
                            name="glueDatabaseName"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.glueDatabaseName}
                            variant="outlined"
                          />
                        </CardContent>
                      </Card>
                      <Card sx={{ mt: 3 }}>
                        <CardHeader title="Governance" />
                        <CardContent>
                          <TextField
                            fullWidth
                            error={Boolean(
                              touched.SamlGroupName && errors.SamlGroupName
                            )}
                            helperText={
                              touched.SamlGroupName && errors.SamlGroupName
                            }
                            label="Team"
                            name="SamlGroupName"
                            onChange={handleChange}
                            select
                            value={values.SamlGroupName}
                            variant="outlined"
                          >
                            {groupOptions.map((group) => (
                              <MenuItem key={group.value} value={group.value}>
                                {group.label}
                              </MenuItem>
                            ))}
                          </TextField>
                        </CardContent>
                        <CardContent>
                          <Autocomplete
                            id="stewards"
                            freeSolo
                            options={groupOptions.map((option) => option.value)}
                            onChange={(event, value) => {
                              setFieldValue('stewards', value);
                            }}
                            renderInput={(renderParams) => (
                              <TextField
                                {...renderParams}
                                label="Stewards"
                                margin="normal"
                                onChange={handleChange}
                                value={values.stewards}
                                variant="outlined"
                              />
                            )}
                          />
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item lg={12} md={6} xs={12}>
                      <Box sx={{ mt: 3 }}>
                        <DatasetLFTagsForm
                          handleDatasetLFTags={setDatasetLFTags}
                        />
                      </Box>
                      <Box
                        sx={{
                          display: 'flex',
                          justifyContent: 'flex-end',
                          mt: 3
                        }}
                      >
                        <LoadingButton
                          color="primary"
                          loading={isSubmitting}
                          type="submit"
                          variant="contained"
                        >
                          Import Dataset
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

export default DatasetImportForm;
