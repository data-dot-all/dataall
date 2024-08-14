import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Divider,
  Tooltip,
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
    <Card {...dataset}>
      <CardHeader title="Governance & Classification" />
      <Divider />
      <CardContent>
        <Box alignItems="center" display="flex">
          <Box sx={{ flexGrow: 1 }}>
            <Typography color="textSecondary" variant="subtitle2">
              Owners
            </Typography>
            <Typography color="textPrimary" variant="body2">
              {dataset.SamlAdminGroupName}
            </Typography>
          </Box>
          {dataset.enableExpiration === true ? (
            <Box>
              <Tooltip title="This is tooltip">
                <Typography
                  align={'right'}
                  color="textSecondary"
                  variant="subtitle2"
                >
                  Expiration Setting for Shares
                </Typography>
              </Tooltip>
              <Typography align={'right'} color="textPrimary" variant="body2">
                {dataset.expirySetting}
              </Typography>
            </Box>
          ) : (
            <Box></Box>
          )}
        </Box>
      </CardContent>
      <CardContent>
        <Box alignItems="center" display="flex">
          <Box sx={{ flexGrow: 1 }}>
            <Typography color="textSecondary" variant="subtitle2">
              Stewards
            </Typography>
            <Typography color="textPrimary" variant="body2">
              {dataset.stewards}
            </Typography>
          </Box>
          {dataset.enableExpiration === true ? (
            <Box>
              <Tooltip title="This is tooltip">
                <Typography
                  align={'right'}
                  color="textSecondary"
                  variant="subtitle2"
                >
                  Expiration duration ( Minimum ) in{' '}
                  {dataset.expirySetting === 'Quarterly'
                    ? 'Quarters'
                    : 'Months'}
                </Typography>
              </Tooltip>
              <Typography align={'right'} color="textPrimary" variant="body2">
                {dataset.expiryMinDuration}
              </Typography>
            </Box>
          ) : (
            <Box></Box>
          )}
        </Box>
      </CardContent>

      <CardContent>
        <Box alignItems="center" display="flex">
          <Box sx={{ flexGrow: 1 }}>
            <Typography color="textSecondary" variant="subtitle2">
              Auto-Approval
            </Typography>
            <Box sx={{ mt: 1 }}>
              <Label color="primary">
                {dataset.autoApprovalEnabled ? 'Enabled' : 'Disabled'}
              </Label>
            </Box>
          </Box>
          {dataset.enableExpiration === true ? (
            <Box>
              <Tooltip title="This is tooltip">
                <Typography
                  align={'right'}
                  color="textSecondary"
                  variant="subtitle2"
                >
                  Expiration duration ( Maximum ) in{' '}
                  {dataset.expirySetting === 'Quarterly'
                    ? 'Quarters'
                    : 'Months'}
                </Typography>
              </Tooltip>
              <Typography align={'right'} color="textPrimary" variant="body2">
                {dataset.expiryMaxDuration}
              </Typography>
            </Box>
          ) : (
            <Box></Box>
          )}
        </Box>
      </CardContent>
      {isFeatureEnabled('datasets_base', 'confidentiality_dropdown') && (
        <CardContent>
          <Typography color="textSecondary" variant="subtitle2">
            Classification
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
              <Chip key={term.nodeUri} label={term.label} variant="outlined" />
            ))}
        </Box>
      </CardContent>
    </Card>
  );
};

DatasetGovernance.propTypes = {
  dataset: PropTypes.object.isRequired
};
