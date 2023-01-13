import React, { useEffect, useRef, useState } from 'react';
import {
  DataSearch,
  MultiList,
  ReactiveBase,
  ReactiveList,
  SelectedFilters
} from '@appbaseio/reactivesearch';
import CircularProgress from '@mui/material/CircularProgress';
import {
  Box,
  Breadcrumbs,
  Button,
  Container,
  Divider,
  Grid,
  Link,
  Paper,
  Popover,
  Typography
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { makeStyles, useTheme } from '@mui/styles';
import { LockOpen } from '@mui/icons-material';
import { Helmet } from 'react-helmet-async';
import * as PropTypes from 'prop-types';
import ChevronRightIcon from '../../icons/ChevronRight';
import PlusIcon from '../../icons/Plus';
import useSettings from '../../hooks/useSettings';
import useToken from '../../hooks/useToken';
import { THEMES } from '../../constants';
import Hit from './Hit';
import ChevronDown from '../../icons/ChevronDown';
import GlossarySearchComponent from './GlossarySearchComponent';
import RequestAccessLFTag from './RequestAccessLFTag';

const useStyles = makeStyles((theme) => ({
  mainSearch: {
    backgroundColor: `${theme.palette.background.paper} !important`,
    color: `${theme.palette.text.primary} !important`,
    titleColor: theme.palette.text.primary,
    borderRadius: theme.shape.borderRadius,
    border: '1px solid rgba(145, 158, 171, 0.24) !important'
  },
  darkListSearch: {
    color: `${theme.palette.background.paper} !important`,
    borderRadius: theme.shape.borderRadius,
    background: `${theme.palette.background.paper} !important`
  },
  lightListSearch: {
    borderRadius: theme.shape.borderRadius,
    background: `${theme.palette.background.paper} !important`
  }
}));

function CatalogFilter(props) {
  const { item, classes, renderNoResults, setFilter } = props;
  const anchorRef = useRef(null);
  const [openMenu, setOpenMenu] = useState(false);
  return (
    <>
      <Button
        color="inherit"
        endIcon={<ChevronDown fontSize="small" />}
        onClick={() => setOpenMenu(!openMenu)}
        ref={anchorRef}
        sx={{
          ml: 2,
          mt: 2,
          mb: 2
        }}
      >
        {item.title}
      </Button>
      <Popover
        anchorEl={anchorRef.current}
        anchorOrigin={{
          horizontal: 'center',
          vertical: 'bottom'
        }}
        getContentAnchorEl={null}
        keepMounted
        onClose={() => setOpenMenu(false)}
        open={openMenu}
      >
        <Box sx={{ p: 3 }}>
          <Typography color="textSecondary" variant="subtitle2">
            <MultiList
              innerClass={{ input: classes.mainSearch }}
              showCheckbox
              showLoadMore={false}
              loader={<CircularProgress size={15} />}
              showMissing={false}
              showFilter
              renderNoResults={renderNoResults}
              filterLabel={item.filterLabel}
              componentId={item.componentId}
              dataField={item.dataField}
              onValueChange={() => setFilter(false)}
            />
          </Typography>
        </Box>
      </Popover>
    </>
  );
}

CatalogFilter.propTypes = {
  item: PropTypes.any,
  classes: PropTypes.any,
  setFilter: PropTypes.func,
  renderNoResults: PropTypes.func
};

function GlossaryFilter(props) {
  const { item, setFilter } = props;
  const anchorRef = useRef(null);
  const [openMenu, setOpenMenu] = useState(false);
  return (
    <>
      <Button
        color="inherit"
        endIcon={<ChevronDown fontSize="small" />}
        onClick={() => {
          setOpenMenu(!openMenu);
          setFilter(false);
        }}
        ref={anchorRef}
        sx={{
          ml: 2,
          mt: 2,
          mb: 2
        }}
      >
        {item.title}
      </Button>
      <Popover
        anchorEl={anchorRef.current}
        anchorOrigin={{
          horizontal: 'center',
          vertical: 'bottom'
        }}
        getContentAnchorEl={null}
        keepMounted
        onClose={() => setOpenMenu(false)}
        open={openMenu}
        PaperProps={{
          sx: { width: 400 }
        }}
      >
        <Box sx={{ p: 3 }}>
          <Typography color="textSecondary" variant="subtitle2">
            <GlossarySearchComponent
              innerClass={{ input: 'mini', list: 'items' }}
            />
          </Typography>
        </Box>
      </Popover>
    </>
  );
}

GlossaryFilter.propTypes = {
  item: PropTypes.any,
  setFilter: PropTypes.func
};
const Catalog = () => {
  const token = useToken();
  const { settings } = useSettings();
  const theme = useTheme();
  const classes = useStyles();
  const anchorRef = useRef(null);
  const [openMenu, setOpenMenu] = useState(false);
  const [filterItems] = useState([
    {
      title: 'Type',
      dataField: 'resourceKind',
      componentId: 'KindSensor',
      filterLabel: 'Type'
    },
    {
      title: 'Tags',
      dataField: 'tags',
      componentId: 'TagSensor',
      filterLabel: 'Tags'
    },
    {
      title: 'Topics',
      dataField: 'topics',
      componentId: 'TopicSensor',
      filterLabel: 'Topics'
    },
    {
      title: 'Region',
      dataField: 'region',
      componentId: 'RegionSensor',
      filterLabel: 'Region'
    },
    {
      title: 'Classification',
      dataField: 'classification',
      componentId: 'ClassificationSensor',
      filterLabel: 'Classification'
    }
  ]);
  const [listClass, setListClass] = useState(
    settings.theme === THEMES.LIGHT
      ? classes.lightListSearch
      : classes.darkListSearch
  );
  const [selectedFiltersCleared, setSelectedFiltersCleared] = useState(true);
  const [isRequestAccessLFTagOpen, setIsRequestAccessLFTagOpen] = useState(false);
  const [isOpeningModal, setIsOpeningModal] = useState(false);

  const handleRequestAccessLFTagModalOpen = () => {
    setIsOpeningModal(true);
    setIsRequestAccessLFTagOpen(true);
  };

  const handleRequestAccessLFTagModalClose = () => {
    setIsRequestAccessLFTagOpen(false);
  };

  const transformRequest = (request) => {
    const transformedRequest = { ...request };
    transformedRequest.url = process.env.REACT_APP_SEARCH_API;
    return {
      ...request,
      url: transformedRequest.url,
      credentials: { token },
      headers: {
        AccessControlAllowOrigin: '*',
        AccessControlAllowHeaders: '*',
        'access-control-allow-origin': '*',
        Authorization: token,
        AccessKeyId: 'None',
        SecretKey: 'None'
      }
    };
  };
  useEffect(() => {
    setListClass(
      settings.theme === THEMES.LIGHT
        ? classes.lightListSearch
        : classes.darkListSearch
    );
  }, [settings.theme, classes]);
  if (!token) {
    return <CircularProgress />;
  }

  return (
    <>
      <Helmet>
        <title>Catalog | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 5
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <Grid
            alignItems="center"
            container
            justifyContent="space-between"
            spacing={3}
          >
            <Grid item>
              <Typography color="textPrimary" variant="h5">
                Catalog
              </Typography>
              <Breadcrumbs
                aria-label="breadcrumb"
                separator={<ChevronRightIcon fontSize="small" />}
                sx={{ mt: 1 }}
              >
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/catalog"
                  variant="subtitle2"
                >
                  Discover
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/catalog"
                  variant="subtitle2"
                >
                  Catalog
                </Link>
              </Breadcrumbs>
            </Grid>
            <Grid item>
              <Box sx={{ m: -1 }}>
                <Button
                  color="primary"
                  component={RouterLink}
                  startIcon={<PlusIcon fontSize="small" />}
                  sx={{ m: 1 }}
                  to="/console/datasets/new"
                  variant="contained"
                >
                  New Dataset
                </Button>
              </Box>
              <Box sx={{ m: -1 }}>
                <Button
                  color="primary"
                  // component={RouterLink}
                  startIcon={<LockOpen fontSize="small" />}
                  sx={{ m: 1 }}
                  variant="contained"
                  onClick={() => handleRequestAccessLFTagModalOpen()}
                >
                  Request Access LF Tag
                </Button>
                {isRequestAccessLFTagOpen && (
                  <RequestAccessLFTag
                    onApply={handleRequestAccessLFTagModalClose}
                    onClose={handleRequestAccessLFTagModalClose}
                    open={isRequestAccessLFTagOpen}
                    stopLoader={() => setIsOpeningModal(false)}
                  />
                )}
              </Box>
            </Grid>
          </Grid>

          <ReactiveBase
            theme={{
              colors: {
                color: theme.palette.text.primary,
                titleColor: theme.palette.text.primary,
                textColor: theme.palette.text.primary,
                backgroundColor: theme.palette.background.default,
                primaryColor: theme.palette.primary.main,
                borderColor: theme.palette.text.secondary
              },
              typography: {
                fontSize: 'small',
                color: theme.palette.text.primary
              }
            }}
            app="dataall-index"
            enableAppbase={false}
            url={process.env.REACT_APP_SEARCH_API}
            transformRequest={transformRequest}
          >
            <Box sx={{ mt: 3 }}>
              <Paper>
                <Box
                  sx={{
                    py: 3,
                    mr: 3,
                    ml: 3
                  }}
                >
                  <DataSearch
                    innerClass={{ input: classes.mainSearch, list: listClass }}
                    autoSuggest
                    showIcon
                    fuzziness="AUTO"
                    componentId="SearchSensor"
                    filterLabel="text"
                    dataField={[
                      'label',
                      'name',
                      'description',
                      'region',
                      'topics',
                      'tags'
                    ]}
                    placeholder="Search"
                  />
                </Box>
                <Divider />
                <Box
                  sx={{
                    mt: 1,
                    mb: 1
                  }}
                >
                  {selectedFiltersCleared ? (
                    <Box sx={{ p: 1 }}>
                      <Typography color="textSecondary" variant="subtitle2">
                        No filters applied
                      </Typography>
                    </Box>
                  ) : (
                    <SelectedFilters />
                  )}
                </Box>
                <Divider />
                <Box
                  sx={{
                    mr: 2
                  }}
                >
                  <Grid container>
                    {filterItems.map((item) => (
                      <Grid item>
                        <CatalogFilter
                          onClick={() => setOpenMenu(!openMenu)}
                          ref={anchorRef}
                          item={item}
                          open={openMenu}
                          classes={classes}
                          setFilter={setSelectedFiltersCleared}
                          renderNoResults={() => <p>No filters found</p>}
                        />
                      </Grid>
                    ))}
                    <Grid item>
                      <GlossaryFilter
                        onClick={() => setOpenMenu(!openMenu)}
                        ref={anchorRef}
                        item={{ title: 'Glossary' }}
                        open={openMenu}
                        classes={classes}
                        setFilter={setSelectedFiltersCleared}
                        renderNoResults={() => <p>No filters found</p>}
                      />
                    </Grid>
                  </Grid>
                </Box>
              </Paper>
            </Box>
            <Grid container spacing={3} sx={{ mt: 1 }}>
              <Grid item key="node1" md={12} xs={12}>
                <ReactiveList
                  react={{
                    and: [
                      'RegionSensor',
                      'SearchSensor',
                      'GlossaryPathSensor',
                      'TagSensor',
                      'TopicSensor',
                      'KindSensor',
                      'ClassificationSensor'
                    ]
                  }}
                  dataField="model"
                  loader={<CircularProgress />}
                  size={8}
                  pagination
                  componentId="SearchResult"
                  render={({ data }) => (
                    <Box>
                      <Grid container spacing={3}>
                        {data.map((hit) => (
                          <Grid item key={hit._id} md={3} xs={12}>
                            <Hit hit={hit} />
                          </Grid>
                        ))}
                      </Grid>
                    </Box>
                  )}
                />
              </Grid>
            </Grid>
          </ReactiveBase>
        </Container>
      </Box>
    </>
  );
};

export default Catalog;
