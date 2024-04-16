import { gql } from 'apollo-boost';
export const isMaintenanceMode = () =>{
    return false;
}
// export const isMaintenanceMode = () => ({
//     query: gql`
//     query isMaintenanceMode {
//         isMaintenanceMode{
//             inMaintenance
//         }
//     }`
// })