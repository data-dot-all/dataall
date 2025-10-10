---
layout: default
title: Maintenance
permalink: /userguide/maintenance/
---

# **Maintenance Window**

When deploying new releases, patch updates, etc there may arise a situation in which a user may be performing an action,  
and, at the same time some AWS resources might be getting updated. This can put data.all created components (Environments, Datasets, Dataset Shares) into broken state.
Also, there might be a need to debug (or patch update few things in data.all) when the data.all administrators may want to restrict actions taken by users in data.all.
In order to protect such a deployment and create a safe environment for deployment / patch updates, data.all 
can be put into maintenance mode. 

In order to enable use of maintenance mode into your deployment of data.all, modify the config.json and add this to the modules section
```js
"maintenance": {
    "active": true
}
```

**Note**: Only data.all administrators can start the maintenance mode. Maintenance window is available in the `Admin Settings` section. 
Data.all currently supports two maintenance modes. 

Read-only : In this mode, a user can visit data.all and navigate through data.all but won't be able to update/modify any data.all related components.
No-Access : In this mode, a user is shown a blank page after the user logs into data.all. In this mode, all user actions are blocked.

**Note** - During both the maintenance modes, data.all admins can perform all data.all actions ( i.e. an admin can login and modify data.all related components where they have access)

The following happens when a maintenance mode / window is started in data.all 

1. All Scheduled ECS tasks ( such as Catalog-Indexer, Share Verifier, etc) are disabled
2. If there is any running ECS task at the time of starting maintenance window, the status of that ECS task is polled and only when all the ECS tasks have completed , the maintenance mode status is changed to ACTIVE - 
indicating that it is safe to deploy or carry out any maintenance activities.
3. GraphQL calls are blocked depending on the maintenance mode. If the maintenance mode is Read-Only, then only mutation graphql calls are blocked. In case of No-Access maintenance mode, both mutation and 
query graphql calls are blocked for the user. 


## **Enable / Disable Maintenance mode** 
In order to enable maintenance mode, goto `Admin Settings` page - which is only accessible to data.all adminstrators - and navigate to the `Maintenance` tab. 
Once you are on the maintenance tab, select the mode and click on `Start Maintenance`.

Please wait for the maintenance window status to change from PENDING to ACTIVE before taking actions. 

You can disable maintenance mode the same way it was enabled by clicking on `End Maintenance`.
