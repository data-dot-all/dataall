import {
  ChevronLeft,
  ChevronRight,
  ShareOutlined,
  BallotOutlined
} from '@mui/icons-material';
import {
  Box,
  Button,
  Divider,
  Drawer,
  IconButton,
  useTheme
} from '@mui/material';
import PropTypes from 'prop-types';
import React, { useEffect, useState } from 'react';
import { AiOutlineExperiment } from 'react-icons/ai';
import * as BiIcons from 'react-icons/bi';
import * as BsIcons from 'react-icons/bs';
import { FiCodesandbox, FiPackage } from 'react-icons/fi';
import { FaDna } from 'react-icons/fa6';
import { MdShowChart } from 'react-icons/md';
import { SiJupyter } from 'react-icons/si';
import { VscBook } from 'react-icons/vsc';
import { useLocation } from 'react-router-dom';
import { ModuleNames, isModuleEnabled } from 'utils';
import { useSettings } from '../../hooks';
import { NavSection } from '../NavSection';
import { Scrollbar } from '../Scrollbar';

export const DefaultSidebar = ({ openDrawer, onOpenDrawerChange }) => {
  const getSections = (isAdvancedMode) => {
    const catalogSection = {
      title: 'Catalog',
      path: '/console/catalog',
      icon: <VscBook size={15} />,
      active: isModuleEnabled(ModuleNames.CATALOG)
    };

    const datasetsSection = {
      title: 'Datasets',
      path: '/console/datasets',
      icon: <FiPackage size={15} />,
      active: isModuleEnabled(ModuleNames.S3_DATASETS)
    };

    const sharesSection = {
      title: 'Shares',
      path: '/console/shares',
      icon: <ShareOutlined size={15} />,
      active: isModuleEnabled(ModuleNames.SHARES)
    };

    const glossariesSection = {
      title: 'Glossaries',
      path: '/console/glossaries',
      icon: <BsIcons.BsTag size={15} />,
      active: isModuleEnabled(ModuleNames.GLOSSARIES)
    };

    const metadataFormSection = {
      title: 'Metadata Forms',
      path: '/console/metadata-forms',
      icon: <BallotOutlined size={15} />,
      active: isModuleEnabled(ModuleNames.METADATA_FORMS)
    };

    const worksheetsSection = {
      title: 'Worksheets',
      path: '/console/worksheets',
      icon: <AiOutlineExperiment size={15} />,
      active: isModuleEnabled(ModuleNames.WORKSHEETS)
    };

    const mlStudioSection = {
      title: 'ML Studio',
      path: '/console/mlstudio',
      icon: <FiCodesandbox size={15} />,
      active: isModuleEnabled(ModuleNames.MLSTUDIO)
    };

    const dashboardsSection = {
      title: 'Dashboards',
      path: '/console/dashboards',
      icon: <MdShowChart size={15} />,
      active: isModuleEnabled(ModuleNames.DASHBOARDS)
    };

    const notebooksSection = {
      title: 'Notebooks',
      path: '/console/notebooks',
      icon: <SiJupyter size={15} />,
      active: isModuleEnabled(ModuleNames.NOTEBOOKS)
    };

    const pipelinesSection = {
      title: 'Pipelines',
      path: '/console/pipelines',
      icon: <BsIcons.BsGear size={15} />,
      active: isModuleEnabled(ModuleNames.DATAPIPELINES)
    };

    const omicsSection = {
      title: 'Omics',
      path: '/console/omics',
      icon: <FaDna size={15} />,
      active: isModuleEnabled(ModuleNames.OMICS)
    };

    const organizationsSection = {
      title: 'Organizations',
      path: '/console/organizations',
      icon: <BiIcons.BiBuildings size={15} />
    };

    const environmentsSection = {
      title: 'Environments',
      path: '/console/environments',
      icon: <BsIcons.BsCloud size={15} />
    };

    let sections = [];

    if (isAdvancedMode) {
      sections = [
        {
          title: 'Discover',
          items: [
            catalogSection,
            datasetsSection,
            sharesSection,
            glossariesSection,
            metadataFormSection
          ]
        },
        {
          title: 'Play',
          items: [
            worksheetsSection,
            notebooksSection,
            mlStudioSection,
            pipelinesSection,
            dashboardsSection,
            omicsSection
          ]
        },
        {
          title: 'Admin',
          items: [organizationsSection, environmentsSection]
        }
      ];
    } else {
      sections = [
        {
          title: 'Discover',
          items: [catalogSection, datasetsSection, sharesSection]
        },
        {
          title: 'Play',
          items: [worksheetsSection, mlStudioSection, dashboardsSection]
        }
      ];
    }

    // Filter out deactivated modules from the sections
    // Note: for backwards compatibility, if the `active` field does not exist, the item is considered active
    sections = sections.map(({ items, ...rest }) => ({
      ...rest,
      items: items.filter((item) => item.active !== false)
    }));

    // If a section does not contain any modules, remove that section
    sections = sections.filter((section) => section.items.length !== 0);

    return sections;
  };

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
      {process.env.REACT_APP_CUSTOM_AUTH ? (
        <div> </div>
      ) : (
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
      )}
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
