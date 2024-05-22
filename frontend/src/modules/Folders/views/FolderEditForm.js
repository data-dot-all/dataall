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
  Container,
  FormHelperText,
  Grid,
  Link,
  TextField,
  Typography
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import * as PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';
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
import { useClient, searchGlossary } from 'services';
import {
  getDatasetStorageLocation,
  updateDatasetStorageLocation
} from '../services';

function FolderEditHeader(props) {
  const { folder } = props;
  return (
    <Grid container justifyContent="space-between" spacing={3}>
      <Grid item>
        <Typography color="textPrimary" variant="h5">
          {`Update Folder: ${folder.label}`}
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
            to={`/console/s3-datasets/${folder.dataset.datasetUri}`}
            variant="subtitle2"
          >
            {folder.dataset.label}
          </Link>
          <Link underline="hover" color="textPrimary" variant="subtitle2">
            <Link
              underline="hover"
              color="textPrimary"
              component={RouterLink}
              to={`/console/s3-datasets/folder/${folder.locationUri}`}
              variant="subtitle2"
            >
              {folder.label}
            </Link>
          </Link>
          <Typography color="textSecondary" variant="subtitle2">
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
            to={`/console/s3-datasets/folder/${folder.locationUri}`}
            variant="outlined"
          >
            Cancel
          </Button>
        </Box>
      </Grid>
    </Grid>
  );
}

FolderEditHeader.propTypes = { folder: PropTypes.object.isRequired };

const FolderEditForm = () => {
  const dispatch = useDispatch();
  const { settings } = useSettings();
  const params = useParams();
  const client = useClient();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const [folder, setFolder] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectableTerms, setSelectableTerms] = useState([]);
  const [folderTerms, setFolderTerms] = useState([]);
  const fetchItem = useCallback(async () => {
    setLoading(true);
    let response = await client.query(getDatasetStorageLocation(params.uri));
    let fetchedTerms = [];
    if (!response.errors && response.data.getDatasetStorageLocation !== null) {
      setFolder(response.data.getDatasetStorageLocation);
      if (
        response.data.getDatasetStorageLocation.terms &&
        response.data.getDatasetStorageLocation.terms.nodes.length > 0
      ) {
        fetchedTerms = response.data.getDatasetStorageLocation.terms.nodes.map(
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
      setFolderTerms(fetchedTerms);
      response = client.query(searchGlossary(Defaults.selectListFilter));
      response.then((result) => {
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
        : 'Dataset folder not found';
      dispatch({ type: SET_ERROR, error });
    }
    setLoading(false);
  }, [dispatch, client, params.uri]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      await client.mutate(
        updateDatasetStorageLocation({
          locationUri: folder.locationUri,
          input: {
            label: values.label,
            description: values.description,
            terms: values.terms.nodes
              ? values.terms.nodes.map((t) => t.nodeUri)
              : values.terms.map((t) => t.nodeUri),
            tags: values.tags
          }
        })
      );
      setStatus({ success: true });
      setSubmitting(false);
      enqueueSnackbar('Folder updated', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      navigate(`/console/s3-datasets/folder/${folder.locationUri}`);
    } catch (err) {
      setStatus({ success: false });
      setErrors({ submit: err.message });
      setSubmitting(false);
      dispatch({ type: SET_ERROR, error: err.message });
    }
  }

  useEffect(() => {
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, dispatch, fetchItem]);

  if (loading) {
    return <CircularProgress />;
  }
  if (!folder) {
    return null;
  }

  return (
    <>
      <Helmet>
        <title>Folder: Folder Update | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 8
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <FolderEditHeader folder={folder} />
          <Box sx={{ mt: 3 }}>
            <Formik
              initialValues={{
                label: folder.label,
                prefix: folder.S3Prefix,
                description: folder.description || '',
                tags: folder.tags || [],
                terms: folder.terms || []
              }}
              validationSchema={Yup.object().shape({
                label: Yup.string()
                  .max(255)
                  .required('*Folder name is required'),
                description: Yup.string().max(5000),
                tags: Yup.array().nullable(),
                terms: Yup.array().nullable()
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
                          <Box sx={{ mb: 2 }}>
                            <TextField
                              error={Boolean(touched.label && errors.label)}
                              fullWidth
                              helperText={touched.label && errors.label}
                              onBlur={handleBlur}
                              onChange={handleChange}
                              label="Folder name"
                              name="label"
                              value={values.label}
                              variant="outlined"
                            />
                          </Box>
                          <Box sx={{ mb: 2 }}>
                            <TextField
                              disabled
                              fullWidth
                              onBlur={handleBlur}
                              onChange={handleChange}
                              label="S3 prefix"
                              name="prefix"
                              value={values.prefix}
                              variant="outlined"
                            />
                          </Box>
                          <Box sx={{ mt: 3 }}>
                            <TextField
                              autoFocus
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
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item lg={4} md={6} xs={12}>
                      <Card>
                        <CardHeader title="Organize" />
                        <CardContent>
                          <Box sx={{ mt: 3 }}>
                            <ChipInput
                              fullWidth
                              variant="outlined"
                              defaultValue={folder.tags}
                              label="Tags"
                              placeholder="Hit enter after typing value"
                              onChange={(chip) => {
                                setFieldValue('tags', [...chip]);
                              }}
                            />
                          </Box>
                          <Box sx={{ mt: 3 }}>
                            {folder && (
                              <Autocomplete
                                multiple
                                id="tags-filled"
                                options={selectableTerms}
                                defaultValue={folderTerms.map((node) => ({
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
                          </Box>
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

export default FolderEditForm;
