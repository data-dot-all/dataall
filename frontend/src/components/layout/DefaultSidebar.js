import React, { useEffect, useState } from 'react';
import * as BsIcons from 'react-icons/bs';
import * as BiIcons from 'react-icons/bi';
import { MdShowChart } from 'react-icons/md';
import { useLocation } from 'react-router-dom';
import PropTypes from 'prop-types';
import {
  Box,
  Button,
  Divider,
  Drawer,
  IconButton,
  useTheme
} from '@mui/material';
import { AiOutlineExperiment } from 'react-icons/ai';
import { FiCodesandbox, FiPackage } from 'react-icons/fi';
import { SiJupyter } from 'react-icons/si';
import { VscBook } from 'react-icons/vsc';
import { ChevronLeft, ChevronRight, ShareOutlined } from '@mui/icons-material';
import NavSection from '../NavSection';
import Scrollbar from '../Scrollbar';
import useSettings from '../../hooks/useSettings';

const DefaultSidebar = (props) => {
  const { openDrawer, onOpenDrawerChange } = props;
  const getSections = (isAdvancedMode) =>
    !isAdvancedMode
      ? [
          {
            title: 'Discover',
            items: [
              {
                title: 'Catalog',
                path: '/console/catalog',
                icon: <VscBook size={15} />
              },
              {
                title: 'Datasets',
                path: '/console/datasets',
                icon: <FiPackage size={15} />
              },
              {
                title: 'Shares',
                path: '/console/shares',
                icon: <ShareOutlined size={10} />
              }
            ]
          },
          {
            title: 'Play',
            items: [
              {
                title: 'Worksheets',
                path: '/console/worksheets',
                icon: <AiOutlineExperiment size={15} />
              },
              {
                title: 'ML Studio',
                path: '/console/mlstudio',
                icon: <FiCodesandbox size={15} />
              },
              {
                title: 'Dashboards',
                path: '/console/dashboards',
                icon: <MdShowChart size={15} />
              }
            ]
          }
        ]
      : [
          {
            title: 'Discover',
            items: [
              {
                title: 'Catalog',
                path: '/console/catalog',
                icon: <VscBook size={15} />
              },
              {
                title: 'Datasets',
                path: '/console/datasets',
                icon: <FiPackage size={15} />
              },
              {
                title: 'Shares',
                path: '/console/shares',
                icon: <ShareOutlined size={15} />
              },
              {
                title: 'Glossaries',
                path: '/console/glossaries',
                icon: <BsIcons.BsTag size={15} />
              }
            ]
          },
          {
            title: 'Play',
            items: [
              {
                title: 'Worksheets',
                path: '/console/worksheets',
                icon: <AiOutlineExperiment size={15} />
              },
              {
                title: 'Notebooks',
                path: '/console/notebooks',
                icon: <SiJupyter size={15} />
              },
              {
                title: 'ML Studio',
                path: '/console/mlstudio',
                icon: <FiCodesandbox size={15} />
              },
              {
                title: 'Pipelines',
                path: '/console/pipelines',
                icon: <BsIcons.BsGear size={15} />
              },
              {
                title: 'Dashboards',
                path: '/console/dashboards',
                icon: <MdShowChart size={15} />
              }
            ]
          },
          {
            title: 'Admin',
            items: [
              {
                title: 'Organizations',
                path: '/console/organizations',
                icon: <BiIcons.BiBuildings size={15} />
              },
              {
                title: 'Environments',
                path: '/console/environments',
                icon: <BsIcons.BsCloud size={15} />
              }
            ]
          }
        ];
  const location = useLocation();
  const { settings } = useSettings();
  const [sections, setSections] = useState(
    getSections(settings.isAdvancedMode)
  );
  const [displayCollapser, setDisplayCollapser] = useState(false);
  const theme = useTheme();

  useEffect(
    () => setSections(getSections(settings.isAdvancedMode)),
    [settings.isAdvancedMode]
  );

  const content = (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100% - 48px)',
        width: '250px'
      }}
    >
      <Scrollbar options={{ suppressScrollX: true }}>
        <Box sx={{ p: 2 }}>
          {sections &&
            sections.map((section) => (
              <NavSection
                key={section.title}
                pathname={location.pathname}
                {...section}
              />
            ))}
        </Box>
      </Scrollbar>
      <Divider />
      <Box sx={{ p: 2 }} style={{ position: 'relative' }}>
        <Box sx={{ pb: 1 }}>
          <Button
            color="primary"
            fullWidth
            sx={{ mt: 3 }}
            onClick={() => {
              window.open(process.env.REACT_APP_USERGUIDE_LINK, '_blank');
            }}
            variant="contained"
          >
            User Guide
          </Button>
        </Box>
      </Box>
    </Box>
  );

  return (
    <>
      <Drawer
        anchor="left"
        open={openDrawer}
        style={{ zIndex: 1250 }}
        PaperProps={{
          sx: {
            backgroundColor: 'background.paper'
          }
        }}
        variant="temporary"
        sx={{
          display: { xs: 'block', sm: 'block', md: 'none' },
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: '100vw' }
        }}
      >
        <Box>
          <IconButton
            onClick={() => {
              onOpenDrawerChange(false);
            }}
          >
            {openDrawer}
            {theme.direction === 'ltr' ? <ChevronLeft /> : <ChevronRight />}
          </IconButton>
        </Box>
        {content}
      </Drawer>
      <Box display={{ xs: 'none', md: 'block' }}>
        <Drawer
          anchor="left"
          open={openDrawer}
          PaperProps={{
            sx: {
              backgroundColor: 'background.paper',
              pt: 8,
              overflow: 'visible'
            }
          }}
          variant="persistent"
          onMouseEnter={() => {
            setDisplayCollapser(true);
          }}
          onMouseLeave={() => {
            setDisplayCollapser(false);
          }}
        >
          {displayCollapser && (
            <Box
              sx={{
                position: 'absolute',
                right: -25,
                top: 100,
                zIndex: 2000,
                backgroundColor: 'background.paper',
                borderColor: `${theme.palette.divider} !important`,
                transform: 'scale(0.7)',
                borderRight: 1,
                borderBottom: 1,
                borderTop: 1,
                borderLeft: 1,
                borderRadius: 50
              }}
            >
              <IconButton
                onClick={() => {
                  onOpenDrawerChange(false);
                }}
              >
                {openDrawer}
                {openDrawer ? <ChevronLeft /> : <ChevronRight />}
              </IconButton>
            </Box>
          )}
          {content}
        </Drawer>
      </Box>
    </>
  );
};

DefaultSidebar.propTypes = {
  openDrawer: PropTypes.bool,
  onOpenDrawerChange: PropTypes.func
};

export default DefaultSidebar;
