import { BugReportOutlined } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import {
  Box,
  CardContent,
  Dialog,
  FormHelperText,
  Switch,
  TextField,
  Typography
} from '@mui/material';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import * as Yup from 'yup';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { startGlueCrawler } from '../services';

export const DatasetStartCrawlerModal = (props) => {
  const { dataset, onApply, onClose, open } = props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      let prefix = '';
      if (values.prefixSpecified && values.prefix) {
        prefix = values.prefix;
      }
      const response = await client.mutate(
        startGlueCrawler({
          datasetUri: dataset.datasetUri,
          input: { prefix }
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Crawler started', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
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
    <Dialog maxWidth="md" fullWidth onClose={onClose} open={open}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h4"
        >
          Crawl dataset
        </Typography>
        <Typography align="center" color="textSecondary" variant="subtitle2">
          <p>
            You can specify an S3 prefix to crawl or toggle off to crawl the
            whole dataset.
          </p>
        </Typography>
        <Box sx={{ p: 3 }}>
          <Formik
            initialValues={{
              prefixSpecified: false,
              prefix: ''
            }}
            validationSchema={Yup.object().shape({
              prefix: Yup.string().when('prefixSpecified', {
                is: true,
                then: Yup.string().max(255).required('Prefix is required')
              })
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
              values
            }) => (
              <form onSubmit={handleSubmit}>
                <Box>
                  <CardContent>
                    <Typography
                      color="textSecondary"
                      gutterBottom
                      variant="subtitle2"
                    >
                      Crawl an Amazon S3 prefix ?
                    </Typography>
                    <Switch
                      color="primary"
                      onChange={handleChange}
                      edge="start"
                      name="prefixSpecified"
                      value={values.prefixSpecified}
                    />
                  </CardContent>
                  {values.prefixSpecified && (
                    <CardContent>
                      <TextField
                        error={Boolean(touched.prefix && errors.prefix)}
                        fullWidth
                        helperText={touched.prefix && errors.prefix}
                        label={`s3://${dataset.restricted.S3BucketName}/`}
                        name="prefix"
                        onBlur={handleBlur}
                        onChange={handleChange}
                        value={values.prefix}
                        variant="outlined"
                      />
                    </CardContent>
                  )}
                </Box>
                {errors.submit && (
                  <Box sx={{ mt: 3 }}>
                    <FormHelperText error>{errors.submit}</FormHelperText>
                  </Box>
                )}
                <CardContent>
                  <LoadingButton
                    fullWidth
                    startIcon={<BugReportOutlined size={15} />}
                    color="primary"
                    disabled={isSubmitting}
                    type="submit"
                    variant="contained"
                  >
                    Start Crawler
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
DatasetStartCrawlerModal.propTypes = {
  dataset: PropTypes.object.isRequired,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired
};
