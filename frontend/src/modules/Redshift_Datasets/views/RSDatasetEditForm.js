import { LoadingButton } from '@mui/lab';
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
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import React, { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom';
import * as Yup from 'yup';
import {
  ArrowLeftIcon,
  ChevronRightIcon,
  ChipInput,
  Defaults,
  useSettings
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { listEnvironmentGroups, searchGlossary, useClient } from 'services';
import { getRedshiftDataset, updateRedshiftDataset } from '../services';
import { ConfidentialityList, Topics } from '../../constants';
import config from '../../../generated/config.json';
import { isFeatureEnabled } from 'utils';

const RSDatasetEditForm = (props) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const params = useParams();
  const { enqueueSnackbar } = useSnackbar();
  const client = useClient();
  const { settings } = useSettings();
  const [loading, setLoading] = useState(true);
  const [dataset, setDataset] = useState(null);
  const [groupOptions, setGroupOptions] = useState([]);
  const [selectableTerms, setSelectableTerms] = useState([]);
  const [tableTerms, setTableTerms] = useState([]);
  const [confidentialityOptions] = useState(
    config.modules.datasets_base.features.confidentiality_dropdown === true &&
      config.modules.datasets_base.features.custom_confidentiality_mapping
      ? Object.keys(
          config.modules.datasets_base.features.custom_confidentiality_mapping
        )
      : ConfidentialityList
  );

  const topicsData = Topics.map((t) => ({ label: t, value: t }));

  const fetchGroups = useCallback(
    async (environmentUri) => {
      try {
        const response = await client.query(
          listEnvironmentGroups({
            filter: Defaults.selectListFilter,
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
    },
    [client, dispatch]
  );

  const fetchItem = useCallback(async () => {
    setLoading(true);
    const response = await client.query(getRedshiftDataset(params.uri));
    if (!response.errors && response.data.getRedshiftDataset !== null) {
      setDataset(response.data.getRedshiftDataset);
      fetchGroups(
        response.data.getRedshiftDataset.environment.environmentUri
      ).catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
      let fetchedTerms = [];
      if (
        response.data.getRedshiftDataset.terms &&
        response.data.getRedshiftDataset.terms.nodes.length > 0
      ) {
        fetchedTerms = response.data.getRedshiftDataset.terms.nodes.map(
          (node) => ({
            label: node.label,
            value: node.nodeUri,
            nodeUri: node.nodeUri,
          disabled: node.__typename !== 'Term' /*eslint-disable-line*/,
            nodePath: node.path,
          nodeType: node.__typename /*eslint-disable-line*/
          })
        );
      }
      setTableTerms(fetchedTerms);
      client.query(searchGlossary(Defaults.selectListFilter)).then((result) => {
        if (
          result.data.searchGlossary &&
          result.data.searchGlossary.nodes.length > 0
        ) {
          const selectables = result.data.searchGlossary.nodes.map((node) => ({
            label: node.label,
            value: node.nodeUri,
            nodeUri: node.nodeUri,
            disabled: node.__typename !== 'Term' /* eslint-disable-line*/,
            nodePath: node.path,
            nodeType: node.__typename /* eslint-disable-line*/
          }));
          setSelectableTerms(selectables);
        }
      });
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Dataset not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  }, [client, dispatch, params.uri, fetchGroups]);

  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, dispatch, fetchItem]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        updateRedshiftDataset({
          datasetUri: dataset.datasetUri,
          input: {
            label: values.label,
            description: values.description,
            tags: values.tags,
            stewards: values.stewards,
            topics: values.topics ? values.topics.map((t) => t.value) : [],
            terms: values.terms.nodes
              ? values.terms.nodes.map((t) => t.nodeUri)
              : values.terms.map((t) => t.nodeUri),
            confidentiality: values.confidentiality,
            autoApprovalEnabled: values.autoApprovalEnabled
          }
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Dataset updated', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        navigate(
          `/console/redshift-datasets/${response.data.updateRedshiftDataset.datasetUri}`
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

  if (loading || !(dataset && dataset.environment)) {
    return <CircularProgress />;
  }

  return (
    <>
      <Helmet>
        <title>Dataset: Dataset Update | data.all</title>
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
                Edit dataset {dataset.label}
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
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to={`/console/redshift-datasets/${dataset.datasetUri}`}
                  variant="subtitle2"
                >
                  {dataset.label}
                </Link>
                <Typography color="textPrimary" variant="subtitle2">
                  Edit
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
                  to={`/console/redshift-datasets/${dataset.datasetUri}`}
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
                label: dataset.label,
                description: dataset.description,
                SamlAdminGroupName: dataset.SamlAdminGroupName,
                topics: dataset.topics?.map((s) => ({ label: s, value: s })),
                tags: dataset.tags,
                terms: dataset.terms || [],
                stewards: dataset.stewards,
                confidentiality: dataset.confidentiality,
                autoApprovalEnabled: dataset.autoApprovalEnabled
              }}
              validationSchema={Yup.object().shape({
                label: Yup.string()
                  .max(255)
                  .required('*Dataset name is required'),
                description: Yup.string().max(5000),
                topics: isFeatureEnabled('datasets_base', 'topics_dropdown')
                  ? Yup.array().min(1).required('*Topics are required')
                  : Yup.array(),
                tags: Yup.array().min(1).required('*Tags are required'),
                confidentiality: isFeatureEnabled(
                  'datasets_base',
                  'confidentiality_dropdown'
                )
                  ? Yup.string()
                      .max(255)
                      .required('*Confidentiality is required')
                  : Yup.string(),
                autoApprovalEnabled: Yup.boolean().required(
                  '*AutoApproval property is required'
                )
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
                        {isFeatureEnabled(
                          'datasets_base',
                          'confidentiality_dropdown'
                        ) && (
                          <CardContent>
                            <TextField
                              fullWidth
                              defaultValue={dataset.confidentiality}
                              error={Boolean(
                                touched.confidentiality &&
                                  errors.confidentiality
                              )}
                              helperText={
                                touched.confidentiality &&
                                errors.confidentiality
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
                        )}
                        {isFeatureEnabled(
                          'datasets_base',
                          'topics_dropdown'
                        ) && (
                          <CardContent>
                            <Autocomplete
                              multiple
                              id="tags-filled"
                              defaultValue={values.topics}
                              options={topicsData}
                              getOptionSelected={(option, value) =>
                                option.value === value.value
                              }
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
                                  error={Boolean(
                                    touched.topics && errors.topics
                                  )}
                                  helperText={touched.topics && errors.topics}
                                />
                              )}
                            />
                          </CardContent>
                        )}
                        <CardContent>
                          {dataset && (
                            <Autocomplete
                              multiple
                              id="tags-filled"
                              options={selectableTerms}
                              defaultValue={tableTerms.map((node) => ({
                                label: node.label,
                                nodeUri: node.nodeUri
                              }))}
                              getOptionLabel={(opt) => opt.label}
                              getOptionDisabled={(opt) => opt.disabled}
                              getOptionSelected={(option, value) =>
                                option.nodeUri === value.nodeUri
                              }
                              onChange={(event, value) => {
                                setFieldValue('terms', value);
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
                                  label="Glossary Terms"
                                />
                              )}
                            />
                          )}
                        </CardContent>
                        <CardContent>
                          <Box>
                            <ChipInput
                              fullWidth
                              defaultValue={dataset.tags}
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
                        <CardContent>
                          {config.modules.datasets_base.features
                            .auto_approval_for_confidentiality_level[
                            values.confidentiality
                          ] === true && (
                            <TextField
                              fullWidth
                              label="Auto Approval"
                              name="autoApprovalEnabled"
                              onChange={handleChange}
                              select
                              value={values.autoApprovalEnabled}
                              variant="outlined"
                            >
                              <MenuItem key={'Enabled'} value={true}>
                                Enabled
                              </MenuItem>
                              <MenuItem key={'Enabled'} value={false}>
                                Disabled
                              </MenuItem>
                            </TextField>
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item lg={5} md={5} xs={12}>
                      <Card sx={{ mb: 3 }}>
                        <CardHeader title="Deployment" />
                        <CardContent>
                          <TextField
                            disabled
                            fullWidth
                            label="Environment"
                            name="environment"
                            value={dataset.environment.label}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            disabled
                            fullWidth
                            label="Region"
                            name="region"
                            value={dataset.environment.region}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            disabled
                            fullWidth
                            label="Organization"
                            name="organization"
                            value={dataset.environment.organization.label}
                            variant="outlined"
                          />
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader title="Governance" />
                        <CardContent>
                          <TextField
                            disabled
                            fullWidth
                            label="Team"
                            name="SamlAdminGroupName"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            variant="outlined"
                            value={dataset.SamlAdminGroupName}
                          />
                        </CardContent>
                        <CardContent>
                          <Autocomplete
                            id="stewards"
                            freeSolo
                            defaultValue={dataset.stewards}
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
                          Save
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

export default RSDatasetEditForm;
