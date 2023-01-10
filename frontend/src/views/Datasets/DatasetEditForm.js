import React, { useCallback, useEffect, useState } from 'react';
import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom';
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
import updateDataset from '../../api/Dataset/updateDataset';
import ChipInput from '../../components/TagsInput';
import TopicsData from '../../components/topics/TopicsData';
import getDataset from '../../api/Dataset/getDataset';
import searchGlossary from '../../api/Glossary/searchGlossary';
import listEnvironmentGroups from '../../api/Environment/listEnvironmentGroups';
import * as Defaults from '../../components/defaults';
// import LFTagEditForm from './LFTagEditForm';

const DatasetEditForm = (props) => {
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
  // const [datasetLFTags, setDatasetLFTags] = useState([]);
  const [confidentialityOptions] = useState([
    'Unclassified',
    'Official',
    'Secret'
  ]);

  const fetchGroups = useCallback(
    async (environmentUri) => {
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
    },
    [client, dispatch]
  );

  const fetchItem = useCallback(async () => {
    setLoading(true);
    const response = await client.query(getDataset(params.uri));
    if (!response.errors && response.data.getDataset !== null) {
      setDataset(response.data.getDataset);
      fetchGroups(response.data.getDataset.environment.environmentUri).catch(
        (e) => dispatch({ type: SET_ERROR, error: e.message })
      );
      let fetchedTerms = [];
      if (
        response.data.getDataset.terms &&
        response.data.getDataset.terms.nodes.length > 0
      ) {
        fetchedTerms = response.data.getDataset.terms.nodes.map((node) => ({
          label: node.label,
          value: node.nodeUri,
          nodeUri: node.nodeUri,
          disabled: node.__typename !== 'Term' /*eslint-disable-line*/,
          nodePath: node.path,
          nodeType: node.__typename /*eslint-disable-line*/
        }));
      }
      setTableTerms(fetchedTerms);
      client.query(searchGlossary(Defaults.SelectListFilter)).then((result) => {
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
        updateDataset({
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
            confidentiality: values.confidentiality
            // lfTagKey: datasetLFTags ? datasetLFTags.map((d) => d.lfTagKey) : [],
            // lfTagValue: datasetLFTags ? datasetLFTags.map((d) => d.lfTagValue) : []
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
        navigate(`/console/datasets/${response.data.updateDataset.datasetUri}`);
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
                  to={`/console/datasets/${dataset.datasetUri}`}
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
                  to={`/console/datasets/${dataset.datasetUri}`}
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
                confidentiality: dataset.confidentiality
              }}
              validationSchema={Yup.object().shape({
                label: Yup.string()
                  .max(255)
                  .required('*Dataset name is required'),
                description: Yup.string().max(5000),
                topics: Yup.array().min(1).required('*Topics are required'),
                tags: Yup.array().min(1).required('*Tags are required'),
                confidentiality: Yup.string().required(
                  '*Confidentiality is required'
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
                        <CardContent>
                          <TextField
                            fullWidth
                            defaultValue={dataset.confidentiality}
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
                            defaultValue={values.topics}
                            options={TopicsData}
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
                                error={Boolean(touched.topics && errors.topics)}
                                helperText={touched.topics && errors.topics}
                              />
                            )}
                          />
                        </CardContent>
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
                    </Grid>
                    <Grid item lg={12} md={6} xs={12}>
                      {/* <Box sx={{ mt: 3 }}>
                        <LFTagEditForm
                          handleLFTags={setDatasetLFTags}
                          tagobject={dataset}
                        />
                      </Box> */}
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

export default DatasetEditForm;
