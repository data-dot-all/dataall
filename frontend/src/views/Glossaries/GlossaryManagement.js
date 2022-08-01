import { Box, CircularProgress, Typography } from '@mui/material';
import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import { makeStyles } from '@mui/styles';
import { LoadingButton, TreeItem, TreeView } from '@mui/lab';
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';
import ArrowRightIcon from '@mui/icons-material/ArrowRight';
import * as BsIcons from 'react-icons/bs';
import Plus from '../../icons/Plus';
import GlossaryNodeForm from './GlossaryNodeForm';
import { useDispatch } from '../../store';
import * as Defaults from '../../components/defaults';
import listGlossaryTree from '../../api/Glossary/listGlossaryTree';
import { SET_ERROR } from '../../store/errorReducer';
import listToTree from '../../utils/listToTree';
import ObjectBrief from '../../components/ObjectBrief';
import GlossaryCreateCategoryForm from './GlossaryCreateCategoryForm';
import GlossaryCreateTermForm from './GlossaryCreateTermForm';

const useTreeItemStyles = makeStyles((theme) => ({
  root: {
    color: theme.palette.text.secondary,
    '&:focus > $content, &$selected > $content': {
      backgroundColor: `var(--tree-view-bg-color, ${theme.palette.grey[400]})`,
      color: 'var(--tree-view-color)'
    },
    '&:focus > $content $label, &:hover > $content $label, &$selected > $content $label':
      {
        backgroundColor: 'transparent'
      }
  },
  content: {
    color: theme.palette.text.secondary,
    borderTopRightRadius: theme.spacing(2),
    borderBottomRightRadius: theme.spacing(2),
    paddingRight: theme.spacing(1),
    fontWeight: theme.typography.fontWeightMedium,
    '$expanded > &': {
      fontWeight: theme.typography.fontWeightRegular
    }
  },
  group: {
    marginLeft: 0,
    '& $content': {
      paddingLeft: theme.spacing(2)
    }
  },
  expanded: {},
  selected: {},
  label: {
    fontWeight: 'inherit',
    color: 'inherit'
  },
  labelRoot: {
    display: 'flex',
    alignItems: 'center',
    padding: theme.spacing(1, 0.5)
  },
  labelIcon: {
    marginRight: theme.spacing(1)
  },
  labelText: {
    fontWeight: 'inherit',
    flexGrow: 1
  }
}));
function StyledTreeItem(props) {
  const classes = useTreeItemStyles();
  const {
    labelText,
    labelIcon: LabelIcon,
    labelInfo,
    color,
    bgColor,
    ...other
  } = props;

  return (
    <TreeItem
      label={
        <div className={classes.labelRoot}>
          <LabelIcon color="inherit" className={classes.labelIcon} />
          <Typography variant="body2" className={classes.labelText}>
            {labelText}
          </Typography>
          <Typography variant="caption" color="inherit">
            {labelInfo}
          </Typography>
        </div>
      }
      style={{
        '--tree-view-color': color,
        '--tree-view-bg-color': bgColor
      }}
      classes={{
        root: classes.root,
        content: classes.content,
        expanded: classes.expanded,
        selected: classes.selected,
        group: classes.group,
        label: classes.label
      }}
      {...other}
    />
  );
}

StyledTreeItem.propTypes = {
  bgColor: PropTypes.string,
  color: PropTypes.string,
  labelIcon: PropTypes.elementType.isRequired,
  labelInfo: PropTypes.string,
  labelText: PropTypes.string.isRequired
};

const useStyles = makeStyles({
  root: {
    height: 264,
    flexGrow: 1,
    maxWidth: 400
  }
});
const GlossaryManagement = (props) => {
  const { glossary, isAdmin, client } = props;
  const dispatch = useDispatch();
  const [fetchingItems, setFetchingItems] = useState(true);
  const [items, setItems] = useState(Defaults.PagedResponseDefault);
  const [nodes, setNodes] = useState([]);
  const classes = useStyles();
  const [data, setData] = useState(glossary);
  const [isTermCreateOpen, setIsTermCreateOpen] = useState(false);
  const [isCategoryCreateOpen, setIsCategoryCreateOpen] = useState(false);

  const handleCategoryCreateModalOpen = () => {
    setIsCategoryCreateOpen(true);
  };

  const handleCategoryCreateModalClose = () => {
    setIsCategoryCreateOpen(false);
  };

  const handleTermCreateModalOpen = () => {
    setIsTermCreateOpen(true);
  };

  const handleTermCreateModalClose = () => {
    setIsTermCreateOpen(false);
  };

  const fetchItems = useCallback(async () => {
    setFetchingItems(true);
    setData(glossary);
    const response = await client.query(
      listGlossaryTree({ nodeUri: glossary.nodeUri, filter: {pageSize: 500} })
    );
    if (!response.errors && response.data.getGlossary !== null) {
      setItems({ ...response.data.getGlossary.tree });
    } else {
      const error = response.errors
        ? response.errors[0].message
        : 'Glossary not found';
      dispatch({ type: SET_ERROR, error });
    }
    setFetchingItems(false);
  }, [glossary, client, dispatch]);

  useEffect(() => {
    if (client) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch, fetchItems]);

  const refreshTree = useCallback(() => {
    const transformedTree = listToTree(
      items.nodes.map((n) => n),
      {
        idKey: 'nodeUri',
        parentKey: 'parentUri'
      }
    );
    setNodes(transformedTree);
  }, [items.nodes]);
  useEffect(() => {
    refreshTree();
  }, [items, refreshTree]);
  const getIcon = (nodeItem) => {
    if (nodeItem.__typename === 'Glossary') {
      return <BsIcons.BsBookmark size={12} />;
    }
    if (nodeItem.__typename === 'Category') {
      return <BsIcons.BsFolder size={12} />;
    }
    return <BsIcons.BsTag size={12} />;
  };

  return (
    <Box
      sx={{
        backgroundColor: 'background.default',
        display: 'flex',
        height: '700px',
        borderRight: 1,
        borderLeft: 1,
        borderTop: 1,
        borderBottom: 1,
        borderColor: 'divider'
      }}
    >
      <Box
        sx={{
          display: 'flex',
          backgroundColor: 'background.paper',
          flexDirection: 'column',
          maxWidth: '100%',
          width: 350,
          height: '100%',
          borderRight: 1,
          borderColor: 'divider'
        }}
      >
        {fetchingItems ? (
          <CircularProgress />
        ) : (
          <TreeView
            className={classes.root}
            defaultExpanded={['3']}
            defaultCollapseIcon={<ArrowDropDownIcon />}
            defaultExpandIcon={<ArrowRightIcon />}
            defaultEndIcon={<div style={{ width: 24 }} />}
          >
            {nodes.map((node) => (
              <StyledTreeItem
                nodeId={node.nodeUri}
                onClick={() => setData(node)}
                labelText={
                  <Box
                    sx={{
                      display: 'flex',
                      ml: 1
                    }}
                  >
                    <Typography
                      sx={{
                        flexGrow: 1,
                        fontWeight: 'inherit'
                      }}
                      variant="body2"
                    >
                      {node.label}
                    </Typography>
                  </Box>
                }
                labelIcon={() => getIcon(node)}
              >
                {node.children &&
                  node.children.map((category) => (
                    <StyledTreeItem
                      nodeId={category.nodeUri}
                      onClick={() => {
                        setData(category);
                      }}
                      labelText={
                        <Box
                          sx={{
                            display: 'flex',
                            ml: 1
                          }}
                        >
                          <Typography
                            sx={{
                              flexGrow: 1,
                              fontWeight: 'inherit'
                            }}
                            variant="body2"
                          >
                            {category.label}
                          </Typography>
                        </Box>
                      }
                      labelIcon={() => getIcon(category)}
                    >
                      {category.children &&
                        category.children.map((term) => (
                          <StyledTreeItem
                            nodeId={term.nodeUri}
                            labelText={
                              <Box
                                sx={{
                                  display: 'flex',
                                  ml: 1
                                }}
                              >
                                <Typography
                                  sx={{
                                    flexGrow: 1,
                                    fontWeight: 'inherit'
                                  }}
                                  variant="body2"
                                >
                                  {term.label}
                                </Typography>
                              </Box>
                            }
                            labelIcon={() => getIcon(term)}
                            color="#1a73e8"
                            bgColor="#e8f0fe"
                            onClick={() => setData(term)}
                          />
                        ))}
                    </StyledTreeItem>
                  ))}
              </StyledTreeItem>
            ))}
          </TreeView>
        )}
      </Box>
      <Box
        sx={{
          backgroundColor: 'background.default',
          display: 'flex',
          flexDirection: 'column',
          flexGrow: 1
        }}
      >
        {isAdmin && (
          <Box
            sx={{
              alignItems: 'center',
              backgroundColor: 'background.paper',
              display: 'flex',
              flexShrink: 0,
              height: 68,
              p: 2,
              borderBottom: 1,
              borderColor: 'divider'
            }}
          >
            <Box sx={{ flexGrow: 1 }} />
            <LoadingButton
              color="primary"
              disabled={data.__typename !== 'Glossary'}
              onClick={handleCategoryCreateModalOpen}
              startIcon={<Plus fontSize="small" />}
              sx={{ m: 1 }}
              variant="outlined"
            >
              Category
            </LoadingButton>
            <LoadingButton
              color="primary"
              disabled={data.__typename === 'Term'}
              onClick={handleTermCreateModalOpen}
              startIcon={<Plus fontSize="small" />}
              sx={{ m: 1 }}
              variant="outlined"
            >
              Term
            </LoadingButton>
          </Box>
        )}
        {fetchingItems ? (
          <CircularProgress />
        ) : (
          <Box>
            {isAdmin && data && (
              <GlossaryNodeForm
                isAdmin={isAdmin}
                refresh={fetchItems}
                nodeType={data.__typename}
                client={client}
                data={data}
              />
            )}
            {!isAdmin && (
              <Box sx={{ p: 3 }}>
                <ObjectBrief
                  uri={data.nodeUri}
                  description={data.description || 'No description provided'}
                  name={data.label}
                />
              </Box>
            )}
          </Box>
        )}
      </Box>
      {isCategoryCreateOpen && (
        <GlossaryCreateCategoryForm
          data={data}
          client={client}
          onApply={handleCategoryCreateModalClose}
          onClose={handleCategoryCreateModalClose}
          refresh={fetchItems}
          isAdmin={isAdmin}
          open={isCategoryCreateOpen}
        />
      )}
      {isTermCreateOpen && (
        <GlossaryCreateTermForm
          data={data}
          client={client}
          onApply={handleTermCreateModalClose}
          onClose={handleTermCreateModalClose}
          refresh={fetchItems}
          isAdmin={isAdmin}
          open={isTermCreateOpen}
        />
      )}
    </Box>
  );
};

GlossaryManagement.propTypes = {
  glossary: PropTypes.object.isRequired,
  isAdmin: PropTypes.bool.isRequired,
  client: PropTypes.func.isRequired
};

export default GlossaryManagement;
