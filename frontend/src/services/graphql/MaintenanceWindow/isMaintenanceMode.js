import { gql } from 'apollo-boost';
export const isMaintenanceMode = () =>{
    return true;
}
// export const isMaintenanceMode = () => ({
//     query: gql`
//     query isMaintenanceMode {
//         isMaintenanceMode{
//             inMaintenance
//         }
//     }`
// })