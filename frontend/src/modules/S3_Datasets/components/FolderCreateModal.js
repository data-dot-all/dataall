import { LoadingButton } from '@mui/lab';
import {
  Autocomplete,
  Box,
  CardContent,
  CardHeader,
  Chip,
  Dialog,
  FormHelperText,
  Grid,
  TextField,
  Typography
} from '@mui/material';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import { useCallback, useEffect, useState } from 'react';
import * as Yup from 'yup';
import { ChipInput, Defaults } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient, addDatasetStorageLocation, searchGlossary } from 'services';

export const FolderCreateModal = (props) => {
  const { dataset, onApply, onClose, open, reloadFolders, ...other } = props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const [selectableTerms, setSelectableTerms] = useState([]);

  const fetchTerms = useCallback(async () => {
    const response = await client.query(
      searchGlossary(Defaults.selectListFilter)
    );
    if (!response.errors) {
      if (
        response.data.searchGlossary &&
        response.data.searchGlossary.nodes.length > 0
      ) {
        const selectables = response.data.searchGlossary.nodes.map((node) => ({
          label: node.label,
          value: node.nodeUri,
          nodeUri: node.nodeUri,
          disabled: node.__typename !== 'Term' /* eslint-disable-line*/,
          nodePath: node.path,
          nodeType: node.__typename /* eslint-disable-line*/
        }));
        setSelectableTerms(selectables);
      }
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  }, [client, dispatch]);
  useEffect(() => {
    if (client) {
      fetchTerms().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch, fetchTerms]);
  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        addDatasetStorageLocation({
          datasetUri: dataset.datasetUri,
          input: {
            label: values.label,
            prefix: values.prefix,
            tags: values.tags,
            description: values.description,
            terms: values.terms.nodes
              ? values.terms.nodes.map((t) => t.nodeUri)
              : values.terms.map((t) => t.nodeUri)
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
        if (reloadFolders) {
          reloadFolders();
        }
        if (onApply) {
          onApply();
        }
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

  if (!dataset) {
    return null;
  }

  return (
    <Dialog maxWidth="lg" fullWidth onClose={onClose} open={open} {...other}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h4"
        >
          Create a new folder
        </Typography>
        <Typography align="center" color="textSecondary" variant="subtitle2">
          Creates an Amazon S3 prefix under the dataset bucket
        </Typography>
        <Box sx={{ p: 3 }}>
          <Formik
            initialValues={{
              label: '',
              prefix: '',
              description: '',
              tags: [],
              terms: []
            }}
            validationSchema={Yup.object().shape({
              label: Yup.string().max(255).required('*Folder name is required'),
              prefix: Yup.string().max(255).required('*Prefix is required'),
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
                    <Box>
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
                    </Box>
                  </Grid>
                  <Grid item lg={4} md={6} xs={12}>
                    <Box>
                      <CardHeader title="Organize" />
                      <CardContent>
                        <ChipInput
                          error={Boolean(touched.tags && errors.tags)}
                          fullWidth
                          helperText={touched.tags && errors.tags}
                          variant="outlined"
                          label="Tags"
                          placeholder="Hit enter after typing value"
                          onChange={(chip) => {
                            setFieldValue('tags', [...chip]);
                          }}
                        />
                      </CardContent>
                      <CardContent>
                        <Autocomplete
                          multiple
                          id="tags-filled"
                          options={selectableTerms}
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
                              fullWidth
                              variant="outlined"
                              label="Glossary Terms"
                            />
                          )}
                        />
                      </CardContent>
                    </Box>
                    {errors.submit && (
                      <Box sx={{ mt: 3 }}>
                        <FormHelperText error>{errors.submit}</FormHelperText>
                      </Box>
                    )}
                  </Grid>
                </Grid>
                <CardContent>
                  <LoadingButton
                    color="primary"
                    fullWidth
                    disabled={isSubmitting}
                    type="submit"
                    variant="contained"
                  >
                    Create folder
                  </LoadingButton>
                </CardContent>
              </form>
            )}
          </Formik>
        </Box>
      </Box>
    </Dialog>
  );
};

FolderCreateModal.propTypes = {
  dataset: PropTypes.object.isRequired,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  reloadFolders: PropTypes.func,
  open: PropTypes.bool.isRequired
};
