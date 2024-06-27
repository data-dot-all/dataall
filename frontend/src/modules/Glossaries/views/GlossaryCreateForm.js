import { LoadingButton } from '@mui/lab';
import Autocomplete from '@mui/lab/Autocomplete';
import {
  Box,
  Breadcrumbs,
  Button,
  Card,
  CardContent,
  CardHeader,
  Container,
  FormHelperText,
  Grid,
  Link,
  TextField,
  Typography
} from '@mui/material';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import React from 'react';
import { Helmet } from 'react-helmet-async';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import * as Yup from 'yup';
import { ArrowLeftIcon, ChevronRightIcon, useSettings } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient, useGroups } from 'services';
import { createGlossary } from '../services';

const GlossaryCreateForm = (props) => {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const { settings } = useSettings();
  const groups = useGroups();

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        createGlossary({
          label: values.label,
          readme: values.readme,
          admin: values.SamlAdminGroupName
        })
      );

      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Glossary created', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        navigate(`/console/glossaries/${response.data.createGlossary.nodeUri}`);
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

  return (
    <>
      <Helmet>
        <title>Glossaries: Glossary Create | data.all</title>
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
                Create a new glossary
              </Typography>
              <Breadcrumbs
                aria-label="breadcrumb"
                separator={<ChevronRightIcon fontSize="small" />}
                sx={{ mt: 1 }}
              >
                <Typography color="textPrimary" variant="subtitle2">
                  Discover
                </Typography>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/glossaries"
                  variant="subtitle2"
                >
                  Glossaries
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/glossaries/new"
                  variant="subtitle2"
                >
                  Create
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
                  to="/console/glossaries"
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
                readme: '',
                tags: []
              }}
              validationSchema={Yup.object().shape({
                label: Yup.string()
                  .max(255)
                  .required('*Glossary name is required'),
                readme: Yup.string()
                  .max(5000)
                  .required('*Glossary readme is required'),
                tags: Yup.array().nullable()
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
                touched,
                values,
                setFieldValue
              }) => (
                <form onSubmit={handleSubmit} {...props}>
                  <Grid container spacing={3}>
                    <Grid item lg={12} md={12} xs={12}>
                      <Card sx={{ mb: 3 }}>
                        <CardHeader title="Details" />
                        <CardContent>
                          <TextField
                            error={Boolean(touched.label && errors.label)}
                            fullWidth
                            helperText={touched.label && errors.label}
                            label="Glossary name"
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
                            helperText={`${
                              200 - values.readme.length
                            } characters left`}
                            label="Short description"
                            name="readme"
                            multiline
                            onBlur={handleBlur}
                            onChange={handleChange}
                            rows={5}
                            value={values.readme}
                            variant="outlined"
                          />
                          {touched.readme && errors.readme && (
                            <Box sx={{ mt: 2 }}>
                              <FormHelperText error>
                                {errors.readme}
                              </FormHelperText>
                            </Box>
                          )}
                        </CardContent>
                        <CardContent>
                          <Autocomplete
                            id="SamlAdminGroupName"
                            disablePortal
                            options={groups}
                            onChange={(event, value) => {
                              if (value) {
                                setFieldValue('SamlAdminGroupName', value);
                              } else {
                                setFieldValue('SamlAdminGroupName', '');
                              }
                            }}
                            inputValue={values.SamlAdminGroupName}
                            renderInput={(params) => (
                              <TextField
                                {...params}
                                fullWidth
                                error={Boolean(
                                  touched.SamlAdminGroupName &&
                                    errors.SamlAdminGroupName
                                )}
                                helperText={
                                  touched.SamlAdminGroupName &&
                                  errors.SamlAdminGroupName
                                }
                                label="Team"
                                onChange={handleChange}
                                name="SamlAdminGroupName"
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
                          Create Glossary
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

export default GlossaryCreateForm;
