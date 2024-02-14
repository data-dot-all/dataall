import PropTypes from 'prop-types';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Typography,
  Divider
} from '@mui/material';
import { Label } from 'design/components/Label';

export const ObjectBrief = (props) => {
  const {
    uri,
    description,
    tags,
    name,
    terms,
    topics,
    title,
    confidentiality,
    ...other
  } = props;

  return (
    <Card {...other}>
      {title && (
        <Box>
          <CardHeader title={title} />
          <Divider />
        </Box>
      )}
      <CardContent>
        <Box>
          {uri && (
            <Box>
              <Typography color="textSecondary" variant="subtitle2">
                URI
              </Typography>
              <Typography color="textPrimary" variant="subtitle2">
                {uri}
              </Typography>
            </Box>
          )}
          <Box sx={{ mt: 3 }}>
            <Typography color="textSecondary" variant="subtitle2">
              Name
            </Typography>
            <Typography color="textPrimary" variant="subtitle2">
              {name}
            </Typography>
          </Box>
          {confidentiality && (
            <Box sx={{ mt: 3 }}>
              <Typography color="textSecondary" variant="subtitle2">
                Classification
              </Typography>
              <Box sx={{ mt: 1 }}>
                <Label color="primary">{confidentiality}</Label>
              </Box>
            </Box>
          )}
          {tags && tags.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography color="textSecondary" variant="subtitle2">
                Tags
              </Typography>
              <Box sx={{ mt: 1 }}>
                {tags?.map((tag) => (
                  <Chip
                    sx={{ mr: 0.5, mb: 0.5 }}
                    key={tag}
                    label={tag}
                    variant="outlined"
                  />
                ))}
              </Box>
            </Box>
          )}
          {topics && topics.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography color="textSecondary" variant="subtitle2">
                Topics
              </Typography>
              <Box sx={{ mt: 1 }}>
                {topics.map((t) => (
                  <Chip
                    sx={{ mr: 0.5, mb: 0.5 }}
                    key={t}
                    label={t}
                    variant="outlined"
                  />
                ))}
              </Box>
            </Box>
          )}
          {terms && terms.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography color="textSecondary" variant="subtitle2">
                Glossary terms
              </Typography>
              <Box sx={{ mt: 1 }}>
                {terms.map((term) => (
                  <Chip
                    key={term.nodeUri}
                    label={term.label}
                    variant="outlined"
                  />
                ))}
              </Box>
            </Box>
          )}
        </Box>
        <Box sx={{ mt: 3 }}>
          <Typography color="textSecondary" variant="subtitle2">
            Description
          </Typography>
          <Typography
            color="textPrimary"
            variant="subtitle2"
            style={{ whiteSpace: 'pre-line' }}
          >
            {description}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

ObjectBrief.propTypes = {
  description: PropTypes.string.isRequired,
  tags: PropTypes.arrayOf(PropTypes.string),
  terms: PropTypes.arrayOf(PropTypes.object),
  name: PropTypes.string.isRequired,
  uri: PropTypes.string.isRequired,
  topics: PropTypes.arrayOf(PropTypes.string),
  title: PropTypes.string,
  confidentiality: PropTypes.string
};
