import { useEffect, useState } from 'react';
import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
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
import { Formik } from 'formik';
import CircularProgress from '@mui/material/CircularProgress';
import { LoadingButton } from '@mui/lab';
import * as PropTypes from 'prop-types';
import { useSnackbar } from 'notistack';
import useSettings from '../../hooks/useSettings';
import ChevronRightIcon from '../../icons/ChevronRight';
import useClient from '../../hooks/useClient';
import ArrowLeftIcon from '../../icons/ArrowLeft';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import getDatasetTable from '../../api/DatasetTable/getDatasetTable';
import searchGlossary from '../../api/Glossary/searchGlossary';
import ChipInput from '../../components/TagsInput';
import updateDatasetTable from '../../api/DatasetTable/updateDatasetTable';
import * as Defaults from '../../components/defaults';
import LFTagEditForm from '../Datasets/LFTagEditForm';

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
            to={`/console/datasets/${table.datasetUri}`}
            variant="subtitle2"
          >
            {table.dataset.name}
          </Link>
          <Link underline="hover" color="textPrimary" variant="subtitle2">
            <Link
              underline="hover"
              color="textPrimary"
              component={RouterLink}
              to={`/console/datasets/table/${table.tableUri}`}
              variant="subtitle2"
            >
              {table.GlueTableName}
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
            to={`/console/datasets/table/${table.tableUri}`}
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

const TableEditForm = () => {
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
  const [tableLFTags, setTableLFTags] = useState([]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      await client.mutate(
        updateDatasetTable({
          tableUri: table.tableUri,
          input: {
            description: values.description,
            terms: values.terms.nodes
              ? values.terms.nodes.map((t) => t.nodeUri)
              : values.terms.map((t) => t.nodeUri),
            tags: values.tags,
            lfTagKey: tableLFTags ? tableLFTags.map((t) => t.lfTagKey) : [],
            lfTagValue: tableLFTags ? tableLFTags.map((t) => t.lfTagValue) : []
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
      navigate(`/console/datasets/table/${table.tableUri}`);
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
      let response = await client.query(getDatasetTable(params.uri));
      let fetchedTerms = [];
      if (!response.errors && response.data.getDatasetTable !== null) {
        setTable(response.data.getDatasetTable);
        if (
          response.data.getDatasetTable.terms &&
          response.data.getDatasetTable.terms.nodes.length > 0
        ) {
          fetchedTerms = response.data.getDatasetTable.terms.nodes.map(
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
        response = client.query(searchGlossary(Defaults.SelectListFilter));
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
                    </Grid>
                    <Grid item lg={12} md={6} xs={12}>
                      <Box sx={{ mt: 3 }}>
                        <LFTagEditForm
                          handleLFTags={setTableLFTags}
                          tagobject={table}
                        />
                      </Box>
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

export default TableEditForm;
