import React, { useState, useEffect } from 'react';
import {
  Typography,
  Button,
  Box,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Dialog,
  CircularProgress
} from '@mui/material';
import { useClient } from 'services';
import { useDispatch } from 'globalErrors';
import { listUserForGroup } from '../../services/graphql/Groups/listUserForGroup';

const UserModal = ({ team, open, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [teamUsers, setTeamUsers] = useState([]);
  const dispatch = useDispatch();
  const client = useClient();

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        setLoading(true);
        const response = await client.query(listUserForGroup(team)); // Use the GraphQL query function to fetch users in Team
        if (response && response.data && response.data.listUsersForGroup) {
          setTeamUsers(response.data.listUsersForGroup);
        }
      } catch (error) {
      } finally {
        setLoading(false);
      }
    };
    if (client && team) {
      fetchUsers();
    }
  }, [dispatch, client, team]);

  return (
    <Dialog maxWidth="lg" onClose={onClose} open={open}>
      <Box
        sx={{
          padding: 10,
          borderRadius: 5,
          minWidth: 800,
          maxHeight: 800,
          overflowY: 'auto'
        }}
      >
        <Typography id="team-members-title" variant="h6" color="textPrimary">
          Team Members
        </Typography>
        {loading ? (
          <Box
            display="flex"
            justifyContent="center"
            alignItems="center"
            minHeight="200px"
          >
            <CircularProgress />
          </Box>
        ) : (
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>User ID</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {teamUsers.map((userId, index) => (
                <TableRow key={index}>
                  <TableCell>
                    <Typography color="textSecondary" variant="body2">
                      {userId}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
        <Box
          sx={{
            mt: 2,
            display: 'flex',
            justifyContent: 'space-between',
            gap: '20px'
          }}
        >
          <Button variant="contained" color="secondary" onClick={onClose}>
            Close
          </Button>
        </Box>
      </Box>
    </Dialog>
  );
};

export { UserModal };
