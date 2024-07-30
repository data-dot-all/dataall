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
import { useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeftIcon,
  ChevronRightIcon,
  ChipInput,
  Defaults,
  useSettings
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { searchGlossary, useClient } from 'services';
import {
  getRedshiftDatasetTable,
  updateRedshiftDatasetTable
} from '../services';

function TableEditHeader(props) {
  const { table } = props;
  return (
    <Grid container justifyContent="space-between" spacing={3}>
      <Grid item>
        <Typography color="textPrimary" variant="h5">
          {`Update Table: ${table.label}`}
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
            to={`/console/redshift-datasets/${table.datasetUri}`}
            variant="subtitle2"
          >
            {table.dataset.name}
          </Link>
          <Link underline="hover" color="textPrimary" variant="subtitle2">
            <Link
              underline="hover"
              color="textPrimary"
              component={RouterLink}
              to={`/console/redshift-datasets/table/${table.rsTableUri}`}
              variant="subtitle2"
            >
              {table.name}
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
            to={`/console/redshift-datasets/table/${table.rsTableUri}`}
            variant="outlined"
          >
            Cancel
          </Button>
        </Box>
      </Grid>
    </Grid>
  );
}

TableEditHeader.propTypes = { table: PropTypes.object.isRequired };

const RSTableEditForm = () => {
  const dispatch = useDispatch();
  const { settings } = useSettings();
  const params = useParams();
  const client = useClient();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const [table, setTable] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectableTerms, setSelectableTerms] = useState([]);
  const [tableTerms, setTableTerms] = useState([]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      await client.mutate(
        updateRedshiftDatasetTable({
          rsTableUri: table.rsTableUri,
          input: {
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
      enqueueSnackbar('Table updated', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      navigate(`/console/redshift-datasets/table/${table.rsTableUri}`);
    } catch (err) {
      console.error(err);
      setStatus({ success: false });
      setErrors({ submit: err.message });
      setSubmitting(false);
      dispatch({ type: SET_ERROR, error: err.message });
    }
  }

  useEffect(() => {
    const fetchItem = async () => {
      setLoading(true);
      let response = await client.query(
        getRedshiftDatasetTable({ rsTableUri: params.uri })
      );
      let fetchedTerms = [];
      if (!response.errors && response.data.getRedshiftDatasetTable !== null) {
        setTable(response.data.getRedshiftDatasetTable);
        if (
          response.data.getRedshiftDatasetTable.terms &&
          response.data.getRedshiftDatasetTable.terms.nodes.length > 0
        ) {
          fetchedTerms = response.data.getRedshiftDatasetTable.terms.nodes.map(
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
        response = client.query(searchGlossary(Defaults.selectListFilter));
        response.then((result) => {
          if (
            result.data.searchGlossary &&
            result.data.searchGlossary.nodes.length > 0
          ) {
            const selectables = result.data.searchGlossary.nodes.map(
              (node) => ({
                label: node.label,
                value: node.nodeUri,
                nodeUri: node.nodeUri,
                disabled: node.__typename !== 'Term' /* eslint-disable-line*/,
                nodePath: node.path,
                nodeType: node.__typename /* eslint-disable-line*/
              })
            );
            setSelectableTerms(selectables);
          }
        });
      } else {
        const error = response.errors
          ? response.errors[0].message
          : 'Dataset table not found';
        dispatch({ type: SET_ERROR, error });
      }
      setLoading(false);
    };
    if (client) {
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, dispatch, params.uri]);

  if (loading) {
    return <CircularProgress />;
  }
  if (!table) {
    return null;
  }

  return (
    <>
      <Helmet>
        <title>Tables: Table Update | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 8
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <TableEditHeader table={table} />
          <Box sx={{ mt: 3 }}>
            <Formik
              initialValues={{
                description: table.description || '',
                tags: table.tags || [],
                terms: table.terms || []
              }}
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
                              disabled
                              fullWidth
                              label="Table name"
                              name="label"
                              value={table.label}
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
                              defaultValue={table.tags}
                              label="Tags"
                              placeholder="Hit enter after typing value"
                              onChange={(chip) => {
                                setFieldValue('tags', [...chip]);
                              }}
                            />
                          </Box>
                          <Box sx={{ mt: 3 }}>
                            {table && (
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
                          Update table
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

export default RSTableEditForm;
