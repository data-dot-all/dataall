import { Box, CardMedia, Grid, Typography } from '@material-ui/core';

const Logo = () => (
  <>
    <Grid
      container
    >
      <Grid
        item
      >
        <Box sx={{ mt: 0.5 }}>
          <CardMedia
            src="/static/logo-dataall.svg"
            component="img"
            sx={{
              height: '25px',
              width: '25px'
            }}
          />
        </Box>
      </Grid>
      <Grid
        item
      >
        <Typography
          variant="h5"
          color="#fff"
        >
            &nbsp;data.all
        </Typography>
      </Grid>
    </Grid>
  </>
);
export default Logo;
