import { Box, Button, Card, Grid, Typography } from '@mui/material';
import PropTypes from 'prop-types';
import { useCardStyle } from 'design';

export const ConsumersListItem = ({ consumer }) => {
  const classes = useCardStyle();

  return (
    <Card
      key={consumer.consumerUri}
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
              Name
            </Typography>
            <Typography
              color="textSecondary"
              variant="body1"
              style={{ wordWrap: 'break-word' }}
            >
              {`${consumer.name}`}
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
              warehouse Identifier
            </Typography>
            <Typography
              color="textSecondary"
              variant="body1"
              style={{ wordWrap: 'break-word' }}
            >
              {`${consumer.warehouseId}`}
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
              warehouse Type
            </Typography>
            <Typography
              color="textSecondary"
              variant="body1"
              style={{ wordWrap: 'break-word' }}
            >
              {`${consumer.warehouseType}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="center" md={1} lg={1} xl={1}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Typography color="textPrimary" variant="body1">
              Team
            </Typography>
            <Typography
              color="textSecondary"
              variant="body1"
              style={{ wordWrap: 'break-word' }}
            >
              {`${consumer.SamlAdminGroupName}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="center" md={1.5} lg={1.5} xl={1.5}>
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
              {`${consumer.type}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="center" md={1.5} lg={1.5} xl={1.5}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Typography color="textPrimary" variant="body1">
              Details
            </Typography>
            <Typography
              color="textSecondary"
              variant="body1"
              style={{ wordWrap: 'break-word' }}
            >
              {`${consumer.content}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="center" md={1} lg={1} xl={1}>
          <Button
            color="primary"
            type="button"
            // TODO implement edit
            //onClick={handleEditModalOpen}
            variant="contained"
          >
            Edit
          </Button>
        </Grid>
        <Grid item justifyContent="center" md={1} lg={1} xl={1}>
          <Button
            color="primary"
            type="button"
            // TODO implement delete
            //onClick={deleteConnection}
            variant="contained"
          >
            Delete
          </Button>
        </Grid>
      </Grid>
    </Card>
  );
};
ConsumersListItem.propTypes = {
  consumer: PropTypes.object.isRequired
};
