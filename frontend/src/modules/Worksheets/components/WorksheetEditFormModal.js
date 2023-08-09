import { LoadingButton } from '@mui/lab';
import {
  Box,
  CardContent,
  CardHeader,
  Dialog,
  FormHelperText,
  Grid,
  TextField,
  Typography
} from '@mui/material';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import * as Yup from 'yup';
import { ChipInput } from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { updateWorksheet } from '../services';

export const WorksheetEditFormModal = (props) => {
  const { worksheet, onApply, onClose, open, reload, ...other } = props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        updateWorksheet({
          worksheetUri: worksheet.worksheetUri,
          input: {
            label: values.label,
            tags: values.tags,
            description: values.description
          }
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Worksheet updated', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        if (reload) {
          reload();
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

  if (!worksheet) {
    return null;
  }

  return (
    <Dialog maxWidth="md" fullWidth onClose={onClose} open={open} {...other}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h4"
        >
          Edit worksheet {worksheet.label}
        </Typography>
        <Box sx={{ p: 3 }}>
          <Formik
            initialValues={{
              label: worksheet.label,
              description: worksheet.description,
              tags: worksheet.tags
            }}
            validationSchema={Yup.object().shape({
              label: Yup.string()
                .max(255)
                .required('*Worksheet name is required'),
              description: Yup.string().max(5000),
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
                    </Box>
                    {errors.submit && (
                      <Box sx={{ mt: 3 }}>
                        <FormHelperText error>{errors.submit}</FormHelperText>
                      </Box>
                    )}
                    <CardContent>
                      <LoadingButton
                        color="primary"
                        disabled={isSubmitting}
                        type="submit"
                        variant="contained"
                      >
                        Save
                      </LoadingButton>
                    </CardContent>
                  </Grid>
                </Grid>
              </form>
            )}
          </Formik>
        </Box>
      </Box>
    </Dialog>
  );
};

WorksheetEditFormModal.propTypes = {
  worksheet: PropTypes.object.isRequired,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  reload: PropTypes.func,
  open: PropTypes.bool.isRequired
};
