import { Box, Button, Card, Grid, Typography } from '@mui/material';
import PropTypes from 'prop-types';
import { useCardStyle } from 'design';
import { Link as RouterLink } from 'react-router-dom';

export const OmicsWorkflowsListItem = ({ workflow }) => {
  const classes = useCardStyle();

  return (
    <Card
      key={workflow.id}
      className={classes.card}
      sx={{
        mt: 2
      }}
    >
      <Grid container spacing={0.5} alignItems="center">
        <Grid item justifyContent="center" md={2} lg={2} xl={2}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Typography color="textPrimary" variant="body1">
              Workflow Id
            </Typography>
            <Typography
              color="textSecondary"
              variant="body1"
              style={{ wordWrap: 'break-word' }}
            >
              {`${workflow.id}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="center" md={4} lg={4} xl={4}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Typography color="textPrimary" variant="body1">
              Name
            </Typography>
            <Typography
              color="textSecondary"
              variant="body1"
              style={{ wordWrap: 'break-word' }}
            >
              {`${workflow.name}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="center" md={2} lg={2} xl={2}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Typography color="textPrimary" variant="body1">
              Type
            </Typography>
            <Typography
              color="textSecondary"
              variant="body1"
              style={{ wordWrap: 'break-word' }}
            >
              {`${workflow.type}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="center" md={4} lg={4} xl={4}>
          <Button
            color="primary"
            type="button"
            component={RouterLink}
            to={`workflows/${workflow.workflowUri}`}
            variant="contained"
          >
            Open Workflow
          </Button>
        </Grid>
      </Grid>
    </Card>
  );
};
OmicsWorkflowsListItem.propTypes = {
  workflow: PropTypes.object.isRequired
};
