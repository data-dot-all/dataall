import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { experimentalStyled } from '@material-ui/core/styles';
import { Box, makeStyles } from '@material-ui/core';
import DefaultNavbar from './DefaultNavbar';
import DefaultSidebar from './DefaultSidebar';
import ErrorNotification from '../ErrorNotification';

const DefaultLayoutRoot = experimentalStyled(Box)(({ theme }) => ({
  ...(theme.palette.mode === 'light' && {
    backgroundColor: theme.palette.background.default,
    display: 'flex',
    height: '100%',
    overflow: 'hidden',
    flexDirection: 'column',
    width: '100%'
  }),
  ...(theme.palette.mode === 'dark' && {
    backgroundColor: theme.palette.background.default,
    display: 'flex',
    height: '100%',
    overflow: 'hidden',
    flexDirection: 'column',
    width: '100%'
  })
}));

const DefaultMain = experimentalStyled(Box)({
  display: 'flex',
  flex: '1 1 auto',
  overflow: 'hidden'
});

const DefaultLayoutContainer = experimentalStyled(Box)({
  display: 'flex',
  flexDirection: 'column'
});

const DefaultLayoutContent = experimentalStyled(Box)({
  flex: '1 1 auto',
  overflow: 'auto',
  WebkitOverflowScrolling: 'touch'
});

const DefaultLayoutWrapper = experimentalStyled(Box)({
  display: 'flex',
  flex: '1 1 auto',
  overflow: 'scroll',
  paddingTop: '64px',
  flexDirection: 'column'
});

const useStyles = makeStyles((theme) => ({
  defaultLayoutWrapper: {
    [theme.breakpoints.up('md')]: {
      paddingLeft: '256px'
    }
  }
}));

const DefaultLayout = () => {
  const [openDrawer, setOpenDrawer] = useState(true);
  const classes = useStyles();

  return (
    <DefaultLayoutRoot>
      <DefaultMain>
        <DefaultNavbar
          openDrawer={openDrawer}
          onOpenDrawerChange={setOpenDrawer}
        />
        <DefaultSidebar
          openDrawer={openDrawer}
          onOpenDrawerChange={setOpenDrawer}
        />
        <DefaultLayoutWrapper className={openDrawer ? classes.defaultLayoutWrapper : null}>
          <DefaultLayoutContainer>
            <DefaultLayoutContent>
              <ErrorNotification />
              <Outlet />
            </DefaultLayoutContent>
          </DefaultLayoutContainer>
        </DefaultLayoutWrapper>
      </DefaultMain>
    </DefaultLayoutRoot>
  );
};

export default DefaultLayout;
