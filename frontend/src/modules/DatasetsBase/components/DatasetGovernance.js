import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Divider,
  Grid,
  Typography
} from '@mui/material';
import PropTypes from 'prop-types';
import { Label } from 'design';
import { isFeatureEnabled } from 'utils';

export const DatasetGovernance = (props) => {
  const { dataset } = props;
  const terms =
    dataset.terms.nodes.length > 0
      ? dataset.terms.nodes
      : [{ label: '-', nodeUri: '-' }];
  const tags = dataset.tags.length > 0 ? dataset.tags : ['-'];

  return (
    <Grid container spacing={2}>
      <Grid item lg={6} xl={6} xs={12}>
        <Card {...dataset}>
          <CardHeader title="Classification" />
          <Divider />
          {isFeatureEnabled('datasets_base', 'confidentiality_dropdown') && (
            <CardContent>
              <Typography color="textSecondary" variant="subtitle2">
                Confidentiality
              </Typography>
              <Box sx={{ mt: 1 }}>
                <Label color="primary">{dataset.confidentiality}</Label>
              </Box>
            </CardContent>
          )}
          {isFeatureEnabled('datasets_base', 'topics_dropdown') && (
            <CardContent>
              <Typography color="textSecondary" variant="subtitle2">
                Topics
              </Typography>
              <Box sx={{ mt: 1 }}>
                {dataset.topics &&
                  dataset.topics.length > 0 &&
                  dataset.topics.map((t) => (
                    <Chip
                      sx={{ mr: 0.5, mb: 0.5 }}
                      key={t}
                      label={t}
                      variant="outlined"
                    />
                  ))}
              </Box>
            </CardContent>
          )}

          <CardContent>
            <Typography color="textSecondary" variant="subtitle2">
              Tags
            </Typography>
            <Box sx={{ mt: 1 }}>
              {tags &&
                tags.map((t) => (
                  <Chip
                    sx={{ mr: 0.5, mb: 0.5 }}
                    key={t}
                    label={t}
                    variant="outlined"
                  />
                ))}
            </Box>
          </CardContent>
          <CardContent>
            <Typography color="textSecondary" variant="subtitle2">
              Glossary terms
            </Typography>
            <Box sx={{ mt: 1 }}>
              {terms &&
                terms.map((term) => (
                  <Chip
                    key={term.nodeUri}
                    label={term.label}
                    variant="outlined"
                  />
                ))}
            </Box>
          </CardContent>
        </Card>
      </Grid>
      <Grid item lg={6} xl={6} xs={12}>
        <Card {...dataset}>
          <CardHeader title="Governance" />
          <Divider />
          <CardContent>
            <Typography color="textSecondary" variant="subtitle2">
              Owners
            </Typography>
            <Typography color="textPrimary" variant="body2">
              {dataset.SamlAdminGroupName}
            </Typography>
          </CardContent>
          <CardContent>
            <Typography color="textSecondary" variant="subtitle2">
              Stewards
            </Typography>
            <Typography color="textPrimary" variant="body2">
              {dataset.stewards}
            </Typography>
          </CardContent>
          <CardContent>
            <Typography color="textSecondary" variant="subtitle2">
              Auto-Approval
            </Typography>
            <Box sx={{ mt: 1 }}>
              <Label color="primary">
                {dataset.autoApprovalEnabled ? 'Enabled' : 'Disabled'}
              </Label>
            </Box>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

DatasetGovernance.propTypes = {
  dataset: PropTypes.object.isRequired
};
