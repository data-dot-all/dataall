import { gql } from 'apollo-boost';

const archiveNotification = ({ notificationUri }) => ({
  variables: {
    notificationUri
  },
  mutation: gql`mutation deleteNotification($notificationUri:String!){
            deleteNotification(notificationUri:$notificationUri)
        }`
});

export default archiveNotification;
