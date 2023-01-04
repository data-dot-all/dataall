# **Shares**
Teams can browse data.all catalog and request access for data assets.
data.all shares data between teams securely within and environment and across environments without any data movement.


Datasets can contain tables and folders. Tables are Glue Tables registered in Glue Catalog.
data.all uses (and automates)
<a href="https://docs.aws.amazon.com/lake-formation/latest/dg/sharing-catalog-resources.html" target="_blank">Lake Formation sharing feature</a>
to create access permissions to tables, meaning that no data is copied between  AWS accounts.

Under-the-hood, folders are prefixes inside the dataset S3 bucket. To create sharing of folders in data.all,
we create an S3 access point per requester group to handle its access to specific prefixes in the dataset.

**Concepts**

- Share request or Share Object: one for each dataset and requester team.
- Share Item refers to the individual tables and folders that are added to the Share request.

**Sharing workflow**

Requesters create a share request and add items to it. Both requesters and approvers can work on this `DRAFT` of
the request and add and remove items to the request Draft. Items that are added go to the `PENDINGAPPROVAL` status. 
Items that are shared and are revoked from the Draft, go to `PENDINGREVOKE` status.

Once the draft is ready, requesters **submit** the request, which moves to the `SUBMITTED` status. 
Then, approvers **approve** or **reject** the request which will go to `APPROVED` or `REJECTED` status. Items also vary their status accordingly.
If the request has been approved, data.all backend triggers the process share task and grants or revoke access to the items approved in the request.

While the backend is processing the task, items stay in `SHARE_IN_PROGRESS` or in `REVOKE_IN_PROGRESS` and the share request is `IN_PROGRESS`.
When all items have been processed the Share object is `COMPLETED` and each of the items has either `SUCCEEDED` or `FAILED`.

New items can be added to the request or revoked from it. Also, both approvers and requesters have the option to **revoke all** 
permissions. With this operation, we remove all grants from tables and folders.

Revoking all permissions still leaves the share request open. Users can delete the share request with the **delete** button.
However, the request cannot contain any shared items. Users must revoke individually or with the revoke all functionality any missing shared items before deletion.


![wf](pictures/shares/shares_sm.png#zoom#shadow)


### **Create a share request (requester)**

On left pane choose **Catalog** then **Search** for the table you want to access. Click on the lock icon of the selected
data asset.

![catalog_search](pictures/shares/shares_1.png#zoom#shadow)

The following window will open. Choose your target environment and team and optionally add a *Request purpose*.

![share_request_form](pictures/shares/share_2_1.png#zoom#shadow)

If instead of to a team, you want to request access for a Consumption role, add it to the request as in the picture below.

![share_request_form](pictures/shares/share_2_2.png#zoom#shadow)

Finally, click on **Send Request**. This will create a share request or object for the corresponding dataset
and if you have requested a table or folder
it will add those items to the request. The share needs to be submitted for the request to be sent to the approvers.

## **Check your sent/received share requests**
Anyone can go to the Shares menu on the left side pane and look up the share requests that they have received
and that they have sent. Click on **Learn More**
in the request that you are interested in to start working on your request. 

![add_share](pictures/shares/shares_completed_inbox.png#zoom#shadow)

## **Add/delete items**
When you create a share request for a dataset, you still need to add the items (tables or folders) that you want to
get access to. Initially the share request should be empty of items and in `DRAFT` state, it should look like the following picture.

![add_share](pictures/shares/shares_initial.png#zoom#shadow)

As appears in the picture, by clicking on **Add Item**, the following window will pop up to let you choose a specific table
or folder in the dataset.

![add_share](pictures/shares/shares_add_window.png#zoom#shadow)

Note that the request is in `DRAFT` status and that
the items that we add are in `PENDINGAPPROVAL`. They are not shared until the request is submitted and processed.

If you have an existing share request with some shared tables and folders, you can add more items
to the request. In the picture below, we have added the *iot* folder to the request and it is now in `PENDINGAPPROVAL`.

To remove an item from the request click on the **Delete** button with 
the trash icon next to it. We can only delete items that have not been shared. Items that are shared must be revoked,
which is explained below. That is why only the Folder *iot* has the **Delete** button next to it.

![add_share](pictures/shares/shares_added.png#zoom#shadow)


## **Revoke Items**
If an item has been previously shared it cannot be directly deleted. First, click on
**Revoke item** next to the item that you want to revoke access to. The item 
will go to `PENDINGREVOKE` status and the request to `DRAFT` status. Access is granted until the request is submitted and processed.

In the example above, we have revoked access to the table *videogames* and the folder *pdfs*.

## **Submit a share request (requester)**

Once the draft is ready, the requesters need to click on the **submit** button. The request should be now in the `SUBMITTED` state. 
Approvers can see the request in their received share requests, alongside the current shared items, revoked items, failed items and pending items.

![accept_share](pictures/shares/shares_submitted_inbox.png#zoom#shadow)

## **Approve/Reject a share request (approver)**

As an approver, click on **Learn more** in the `SUBMITTED` request and in the share view you can check the tables and folders added or revoked in the request.
This is the view that approvers see, it now contains buttons to approve or reject the request.

![submit_share_2](pictures/shares/shares_submitted.png#zoom#shadow)

If the approver **approves** the request, it moves to the `APPROVED` status. Share items will go to `SHARE_APPROVED` and `REVOKE_APPROVED`
depending on their previous state. Data.all starts a process share task, during the handling of the shares, items and the request
are `*IN_PROGRESS` states. 

![accept_share](pictures/shares/shares_approved.png#zoom#shadow)

When the task is completed, the items go to `*SUCCEEDED` or `*FAILED` and the request is `COMPLETED`.

![accept_share](pictures/shares/shares_completed.png#zoom#shadow)

!!!info "delete after revoke"
    Items that were shared and have been revoked and are in `REVOKE_SUCCEEDED` status
    can now be deleted from the share request.

If a dataset is shared, the requester should see the dataset on his or her screen. The role with
regards to the dataset is `SHARED`.

![accept_share](pictures/shares/shares_dataset.png#zoom#shadow)


## **Revoke all items**
After a project or during clean-up tasks we might want to clean up all shares in a request.
Approvers and requesters have access to the **Revoke all** button, that deletes all items
that are not shared and revokes all shared items. 


Here we have an example of a request before being completely revoked:

![accept_share](pictures/shares/shares_revokeall_1.png#zoom#shadow)

And after revoking all, the only left items are those that have been revoked. 
If we click again on the revoke all button they will be deleted.

![accept_share](pictures/shares/shares_revokeall_2.png#zoom#shadow)

## **Delete share request**
To delete a share request, it needs to be empty from shared items.
For example, the following request has some items in `SHARE_SUCCEEDED` and `PENDINGREVOKE` state, therefore
we receive an error.

![share](pictures/shares/shares_delete_unauth.png#zoom#shadow)


Once we have revoked access to all items (by using revoke all for example) we can delete the request.

!!! success "Proactive clean-up"
    If there are no more shared folders or tables in a share request, data.all automatically cleans up any 
    missing S3 access point or Lake Formation permission.

## **Consume shared data**
Data.all tables are Glue tables shared using AWS Lake Formation, therefore any service that reads Glue tables and integrates
with Lake Formation is able to consume the data. Permissions are granted to the team role or the consumption role that 
has been specified in the request.

For the case of folders, the underlying sharing mechanism used is S3 Access Points. You can read data inside a prefix using 
the IAM role of the requester (same as with tables) and executing get calls to the S3 access point.

For example:
```json
 aws s3 ls arn:aws:s3:<SOURCE_REGION>:<SOURCE_AWSACCOUNTID>:accesspoint/<DATASETURI>-<REQUESTER-TEAM>/folder2/
```

[//]: # (### **Use data subscriptions**)

[//]: # (data.all helps data owners publish notification updates to all their data consumers.)

[//]: # (It also helps data consumers react to new data shared by the owners.)

[//]: # ()
[//]: # (#### Step 1: Enable subscriptions on the environment)

[//]: # ()
[//]: # (Check the <a href="environments.html">environment</a> documentation for the steps to enable subscriptions.)

[//]: # ()
[//]: # (!!!abstract "AWS SNS Topics")

[//]: # (    When subscriptions are enabled, **as a data producer you can publish a message** to the producers SNS topic.)

[//]: # (    You can also **subscribe to data consumers SNS topic** to be aware of the latest data updates from the producers.)

[//]: # ()
[//]: # (#### Step 2: Publish notification update)

[//]: # (**IMPORTANT**)

[//]: # ()
[//]: # (This feature is disabled at the moment)

