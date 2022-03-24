import { Link as RouterLink, useNavigate } from 'react-router-dom';
import * as Yup from 'yup';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
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
  MenuItem,
  TextField,
  Typography
} from '@material-ui/core';
import { Helmet } from 'react-helmet-async';
import { LoadingButton } from '@material-ui/lab';
import useClient from '../../hooks/useClient';
import ChevronRightIcon from '../../icons/ChevronRight';
import ArrowLeftIcon from '../../icons/ArrowLeft';
import useSettings from '../../hooks/useSettings';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import ChipInput from '../../components/TagsInput';
import useGroups from '../../hooks/useGroups';
import { createWorksheet } from '../../api/Worksheet';

const WorksheetCreateForm = (props) => {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const groups = useGroups();
  const { settings } = useSettings();
  const groupOptions = groups ? groups.map((g) => ({ value: g, label: g })) : [];

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(createWorksheet({
        label: values.label,
        description: values.description,
        SamlAdminGroupName: values.SamlGroupName,
        tags: values.tags
      }));
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Worksheet created', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        navigate(`/console/worksheets/${response.data.createWorksheet.worksheetUri}`);
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
        <title>Worksheets: Worksheet Create | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 8
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <Grid
            container
            justifyContent="space-between"
            spacing={3}
          >
            <Grid item>
              <Typography
                color="textPrimary"
                variant="h5"
              >
                Create a new worksheet
              </Typography>
              <Breadcrumbs
                aria-label="breadcrumb"
                separator={<ChevronRightIcon fontSize="small" />}
                sx={{ mt: 1 }}
              >
                <Typography
                  color="textPrimary"
                  variant="subtitle2"
                >
                  Play
                </Typography>
                <Link
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/worksheets"
                  variant="subtitle2"
                >
                  Worksheets
                </Link>
                <Link
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/worksheets/new"
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
                  to="/console/worksheets"
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
                SamlGroupName: '',
                tags: []
              }}
              validationSchema={Yup
                .object()
                .shape({
                  label: Yup.string().max(255).required('*Worksheet name is required'),
                  description: Yup.string().max(5000),
                  SamlGroupName: Yup.string().max(255).required('* Team is required'),
                  tags: Yup.array().nullable()
                })}
              onSubmit={async (values, { setErrors, setStatus, setSubmitting }) => {
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
                <form
                  onSubmit={handleSubmit}
                  {...props}
                >
                  <Grid
                    container
                    spacing={3}
                  >
                    <Grid
                      item
                      lg={7}
                      md={6}
                      xs={12}
                    >
                      <Card sx={{ mb: 3 }}>
                        <CardHeader title="Details" />
                        <CardContent>
                          <TextField
                            error={Boolean(touched.label && errors.label)}
                            fullWidth
                            helperText={touched.label && errors.label}
                            label="Worksheet name"
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
                            helperText={`${200 - values.description.length} characters left`}
                            label="Short description"
                            name="description"
                            multiline
                            onBlur={handleBlur}
                            onChange={handleChange}
                            rows={5}
                            value={values.description}
                            variant="outlined"
                          />
                          {(touched.description && errors.description) && (
                            <Box sx={{ mt: 2 }}>
                              <FormHelperText error>
                                {errors.description}
                              </FormHelperText>
                            </Box>
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid
                      item
                      lg={5}
                      md={6}
                      xs={12}
                    >
                      <Card>
                        <CardHeader title="Organize" />
                        <CardContent>
                          <TextField
                            fullWidth
                            error={Boolean(touched.SamlGroupName && errors.SamlGroupName)}
                            helperText={touched.SamlGroupName && errors.SamlGroupName}
                            label="Team"
                            name="SamlGroupName"
                            onChange={handleChange}
                            select
                            value={values.SamlGroupName}
                            variant="outlined"
                          >
                            {groupOptions.map((group) => (
                              <MenuItem
                                key={group.value}
                                value={group.value}
                              >
                                {group.label}
                              </MenuItem>
                            ))}
                          </TextField>
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
                                setFieldValue('tags', [
                                  ...chip
                                ]);
                              }}
                            />
                          </Box>
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
                          pending={isSubmitting}
                          type="submit"
                          variant="contained"
                        >
                          Create Worksheet
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

export default WorksheetCreateForm;
