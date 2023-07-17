import { Box, CardMedia, Grid, Typography } from '@mui/material';

const Logo = () => (
  <>
    <Grid container>
      <Grid item>
        <Box sx={{ mt: 0.5 }}>
          <CardMedia
            src="/static/logo-dataall.svg"
            component="img"
            sx={{
              height: '25px',
              width: '35px'
            }}
          />
        </Box>
      </Grid>
      <Grid item>
        <Typography variant="h5" color="#fff">
          &nbsp;data.all
        </Typography>
      </Grid>
    </Grid>
  </>
);
export default Logo;
