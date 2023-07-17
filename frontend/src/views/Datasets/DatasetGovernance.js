import PropTypes from 'prop-types';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Divider,
  Typography
} from '@mui/material';
import Label from '../../components/Label';

const DatasetGovernance = (props) => {
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
          Classification
        </Typography>
        <Box sx={{ mt: 1 }}>
          <Label color="primary">{dataset.confidentiality}</Label>
        </Box>
      </CardContent>
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

export default DatasetGovernance;
