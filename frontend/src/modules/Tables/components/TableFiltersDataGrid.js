import { Card, CardContent, CircularProgress, Typography } from '@mui/material';
import { DataGrid, GridActionsCellItem } from '@mui/x-data-grid';
import { Warning } from '@mui/icons-material';
import PropTypes from 'prop-types';
import React, { useState } from 'react';

import { DeleteObjectWithFrictionModal } from 'design';

import DeleteIcon from '@mui/icons-material/DeleteOutlined';
import { useTheme } from '@mui/styles';

export const TableFiltersDataGrid = ({
  items,
  filter,
  loading,
  handlePageSizeChange,
  handlePageChange,
  deleteFunction,
  assignFunction,
  ...other
}) => {
  const theme = useTheme();
  const [isDeleteFilterModalOpenId, setIsDeleteFilterModalOpen] = useState(0);

  const handleDeleteFilterModalOpen = (id) => {
    setIsDeleteFilterModalOpen(id);
  };
  const handleDeleteFilterModalClosed = () => {
    setIsDeleteFilterModalOpen(0);
  };

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <DataGrid
      autoHeight
      sx={{
        wordWrap: 'break-word', //TODO: create a generic styled datagrid to be used across features
        '& .MuiDataGrid-row': {
          borderBottom: '1px solid rgba(145, 158, 171, 0.24)'
        },
        '& .MuiDataGrid-columnHeaders': {
          borderBottom: 0.5
        },
        '&.MuiDataGrid-root--densityStandard .MuiDataGrid-cell': {
          py: '15px'
        },
        '& .MuiDataGrid-cell:hover': {
          color: theme.palette.primary.main
        }
      }}
      showCellVerticalBorder
      showColumnVerticalBorder
      showColumnRightBorder
      showCellRightBorder
      getRowId={(node) => node.filterUri}
      rows={items.nodes}
      columns={[
        { field: 'id', hide: true },
        {
          field: 'label',
          headerName: 'Filter Name',
          flex: 1,
          editable: false
        },
        {
          field: 'description',
          headerName: 'Description',
          flex: 1,
          editable: false
        },
        {
          field: 'filterType',
          headerName: 'Filter Type',
          flex: 0.5,
          editable: false
        },
        {
          field: 'includedCols',
          headerName: 'Included Columns',
          flex: 1,
          editable: false
        },
        {
          field: 'rowExpression',
          headerName: 'Row Expression',
          flex: 1,
          editable: false
        },
        {
          field: 'actions',
          headerName: 'Actions',
          flex: 0.5,
          type: 'actions',
          cellClassName: 'actions',
          getActions: ({ id, ...props }) => {
            const name = props.row.label;
            return [
              <GridActionsCellItem
                icon={<DeleteIcon />}
                label="Delete"
                onClick={() => handleDeleteFilterModalOpen(id)}
                color="inherit"
              />,
              <DeleteObjectWithFrictionModal
                objectName={name}
                onApply={() => handleDeleteFilterModalClosed()}
                onClose={() => handleDeleteFilterModalClosed()}
                open={isDeleteFilterModalOpenId === id}
                isAWSResource={false}
                deleteFunction={() => deleteFunction(id)}
                deleteMessage={
                  <Card variant="outlined" sx={{ mb: 2 }}>
                    <CardContent>
                      <Typography variant="subtitle2" color="error">
                        <Warning sx={{ mr: 1 }} /> Revoke all share items where
                        data filter <b>{name}</b> is used before proceeding with
                        the deletion !
                      </Typography>
                    </CardContent>
                  </Card>
                }
              />
            ];
          }
        }
      ]}
      rowCount={items.count}
      page={items.page - 1}
      pageSize={filter.pageSize}
      paginationMode="server"
      onPageChange={handlePageChange}
      onPageSizeChange={(pageSize) => handlePageSizeChange(pageSize)}
      loading={loading}
      getRowHeight={() => 'auto'}
      disableSelectionOnClick
    />
  );
};

TableFiltersDataGrid.propTypes = {
  items: PropTypes.object.isRequired,
  filter: PropTypes.object.isRequired,
  loading: PropTypes.bool.isRequired,
  handlePageSizeChange: PropTypes.func,
  handlePageChange: PropTypes.func,
  deleteFunction: PropTypes.func,
  assignFunction: PropTypes.func
};
