# **Shares**
Teams can browse data.all catalog and request access for data assets.
data.all shares data between teams securely within and environment and across environments without any data movement.

**Concepts**

- Share request or Share Object: one for each dataset and requester team.
- Share Item refers to the individual Redshift table, Glue table, folder or S3 Bucket that is added to the Share request.

**Shareable items**

In data.all there are 2 types of datasets: S3 Datasets and Redshift Datasets. Here is an overview of the items that can
be shared using data.all by type of dataset. A detailed explanation of the technical details for each type can be found 
in the AWS data sharing technical details section.

- From S3 Datasets we can share:
     - S3 Bucket of the Dataset - using IAM permissions and S3/KMS policies
     - one or multiple Glue Tables (Tables) - using [Lake Formation](<a href="https://docs.aws.amazon.com/lake-formation/latest/dg/sharing-catalog-resources.html" target="_blank">Lake Formation sharing feature</a>) to create access permissions to tables, meaning that no data is copied between AWS accounts.
     - one or multiple S3 Prefixes (Folders) - using S3 access points to manage granular S3 policies.
- From Redshift Datasets we can share:
     - one or multiple Redshift Tables - using Redshift datashares

**Sharing workflow**

Requesters create a share request and add items to it. Both requesters and approvers can work on this `DRAFT` of
the request and add and delete items to the request Draft. Items that are added go to the `PENDINGAPPROVAL` status.

Once the draft is ready, requesters **submit** the request, which moves to the `SUBMITTED` status. 
Then, approvers **approve** or **reject** the request which will go to `APPROVED` or `REJECTED` status and its
items to `SHARE_APPROVED` or `SHARE_REJECTED` correspondingly.

When the sharing task starts in the backend, both items and the share object move to `SHARE_IN_PROGRESS`.
Once all items have been processed, the Share object is `PROCESSED` and each of the items is in either `SHARE_SUCCEEDED` or `SHARE_FAILED`. 
New items can be added to the share requests, the request will go back to `DRAFT` to be re-processed.

Both approvers and requesters can revoke access to shared items. They open the revoke items window and select which items 
should be revoked from the share request. The items move to `REVOKE_APPROVED` while the share is in `REVOKED` status.

While the revoking task is executing, the items and the request remain in `REVOKE_IN_PROGRESS` until
the revoke is complete and items go to `REVOKE_FAILED` or `SUCCEEDED`. If there are share items in `PENDINGAPPROVAL` 
in the share request, it will go back to `DRAFT`. Otherwise, it will go to `PROCESSED`.

Requesters can delete the share request with the **delete** button.
However, the request cannot contain any shared items. Users must revoke all shared items before deletion.


![wf](pictures/shares/share_sm.png#zoom#shadow)


## **Create a share request (requester)**

On left pane choose **Catalog** then **Search** for the table you want to access. Click on the lock icon of the selected
data asset.

![catalog_search](pictures/shares/shares_1.png#zoom#shadow)

The following window will open. Choose your target environment and team.

![share_request_form](pictures/shares/shares_2_1.png#zoom#shadow)

If instead of to a team, you want to request access for a Consumption role, add it to the request as in the picture below. 

<b><i>NOTE: </i></b> If the consumption role selected is not data.all managed - you will have the option to allow data.all to attach the share policies to the consumption role for this particular share object (if not enabled here you will have to manually attach the share policies to be given access to data).

![share_request_form](pictures/shares/shares_2_2.png#zoom#shadow)

Finally, click on **Create Draft Request**. This will create a share request or object for the corresponding dataset
and if you have requested a table or folder it will add those items to the request. 
After that the modal window will switch to share edit form.
![share_request_form](pictures/shares/shares_2_3.png#zoom#shadow)

Here you can edit the list of items you want to request access to. Note that the request is in `DRAFT` status and that
the items that we add are in `PENDINGAPPROVAL`. They are not shared until the request is submitted and processed.
The share can not be submitted if the list of items is empty. 

`Request purpose` is optional field, recommended length is up to 200 symbols.

When you are happy with the share request form, click **Submit Request** or click **Draft Request** if you want to return to this form later.

The share needs to be submitted for the request to be sent to the approvers.

## **Check your sent/received share requests**
Anyone can go to the Shares menu on the left side pane and look up the share requests that they have received
and that they have sent. Click on **Learn More**
in the request that you are interested in to start working on your request. 

![add_share](pictures/shares/shares_inbox.png#zoom#shadow)

## **Add/delete items**
If the request is not being processed, it can be edited by clicking the **Edit** button on top of the page.
![edit_share](pictures/shares/shares_view.png#zoom#shadow)
**Edit** button opens the modal window with the Share Edit Form, same as upon creating the share.
Here you can edit list of shared items and request purpose.
To remove an item from the request click on the **Delete** button with 
the trash icon next to it. We can only delete items that have not been shared. Items that are shared must be revoked,
which is explained below.

## **Submit a share request (requester)**

Once the draft is ready, the requesters need to click on the **submit** button. The request should be now in the `SUBMITTED` state. 
Approvers can see the request in their received share requests, alongside the current shared items, revoked items, failed items and pending items.

![submit_share_2](pictures/shares/shares_outbox.png#zoom#shadow)

## (Optional Pre-Approval Work) Adding Filters to Glue Table Share Items (approver)

As an approver, you will also see the option to **Edit Filters** for Glue Table share items:

![share_table_filter](pictures/shares/share_table_filter.png#zoom#shadow)

Here an approver can attach one or more filters that were created on the table previously to the table:

![share_table_filter_edit](pictures/shares/share_table_filter_edit.png#zoom#shadow)

Once assigned, the filter will appear in the share object view and can be clicked on to view the underlying associated data filters assigned

![share_table_filter_attached](pictures/shares/share_table_filter_attached.png#zoom#shadow)

![share_table_filter_view](pictures/shares/share_table_filter_view.png#zoom#shadow)

Before sharing as the table - approvers can also edit the assigned filter and remove underlying data filters or attach new ones as needed. Once the share is approved there is no longer the ability to edit filters and the table item must be revoked and re-shared to assign new filters.

**NOTE:** If more than 1 filter is assigned to a table share item, the resulting data access is evaluated as the union (logical 'OR') of the filters assigned. 

**NOTE:** If assigning filter(s) to a table share item, the **Item Filter Name** specified will be used in naming the table resource link for the consumer, meaning the consumer will be reading for table named - `tablename_filtername`


## **Approve/Reject a share request (approver)**

As an approver, click on **Learn more** in the `SUBMITTED` request and in the share view you can check the tables and folders added in the request.
This is the view that approvers see, it now contains buttons to approve or reject the request.

![submit_share_2](pictures/shares/shares_submitted.png#zoom#shadow)

If the approvers **approve** the request, it moves to the `APPROVED` status. Share items IN `PENDINGAPPROVAL` will go to `SHARE_APPROVED`. 

![accept_share](pictures/shares/shares_approved.png#zoom#shadow)

Data.all backend starts a sharing task, during which, items and the request
are in `SHARE_IN_PROGRESS` state. 

![accept_share](pictures/shares/shares_in_progress.png#zoom#shadow)

When the task is completed, the items go to `SHARE_SUCCEEDED` or `SHARE_FAILED` and the request is `PROCESSED`. To understand
what happens under-the-hood when each share item is processed, check out the AWS data sharing technical details section.

![accept_share](pictures/shares/shares_completed.png#zoom#shadow)


If a dataset is shared, requesters should see the dataset on their screens. Their role with
regards to the dataset is `SHARED`.

![accept_share](pictures/shares/shares_dataset.png#zoom#shadow)

## **Verify (and Re-apply) Items**

As of V2.3 of data.all - share requestors or approvers are able to verify the health status of the share items within their share request from the data.all UI. Any set of share items that are in a shared state (i.e. `SHARE_SUCCEEDED` or `REVOKE_FAILED` state) will be able to be selected to start a verify share process.

![share_verify](pictures/shares/share_verify.png#zoom#shadow)

Upon completion of the verify share process, each share item's healthStatus will be updated with an updated healthStatus (i.e. `Healthy` or `Unhealthy`) as well as a timestamp representing the last verification time. If the share item is in an `Unhealthy` health status, there will also be included a health message detailing what part of the share is in an unhealthy state.

In addition to running a verify share process on particular items, dataset owners can run the verify share process on multiple share objects associated with a particular dataset. Navigating to the Dataset --> Shares Tab, dataset owners can start a verify process on multiple share objects. For each share object selected, the share items that are in a shared state for the associated share object will verified and updated with a new health status and so on.

![share_verify](pictures/shares/share_verify_dataset.png#zoom#shadow)

!!! success "Scheduled Share Verify Task"
    The share verifier process is run against all share object items that are in a shared state every 7 days by default
    as a scheduled task which runs in the background of data.all.

If any share items do end up in an `Unhealthy` status, the data.all approver will have the option to re-apply the share for the selected items that are in an unhealthy state.

![share_reapply](pictures/shares/share_reapply.png#zoom#shadow)

Upon successful re-apply process, the share items health status will revert back to a `Healthy` status with an updated timestamp.

## **Revoke Items**
Both approvers and requesters can click on the button **Revoke items** to remove the share grant from chosen items.


It will open a window where multiple items can be selected for revoke. Once the button "revoke selected items" is
pressed the consequent revoke task will be triggered.

![accept_share](pictures/shares/shares_revoke.png#zoom#shadow)

!!! success "Proactive clean-up"
    In every revoke task, data.all checks if there are no more shared folders or tables in a share request.
    In such case, data.all automatically cleans up any unnecessary S3 access point or Lake Formation permission.

## **View Share Logs**
For the share Approvers the logs of share processor are available via Data.all UI. To view logs of the latest share processor run, 
click **Logs** button in right upper conner of the Share View page.
![accept_logs](pictures/shares/shares_logs.png#zoom#shadow)


## **Delete share request**
To delete a share request, it needs to be empty from shared items.
For example, the following request has some items in `SHARE_SUCCEEDED` state, therefore
we receive an error. Once we have revoked access to all items we can delete the request.

![share](pictures/shares/shares_delete_unauth.png#zoom#shadow)

## **AWS data sharing technical details**
Here is a brief explanation of how each type of sharing mechanism is implemented in data.all. It is important to 
understand what really happens in AWS when dealing with downstream integrations that will consume shared data.

### S3 Bucket sharing
In this type of share the permissions are granted to the IAM role specified in the request as principal. It 
can be either a data.all team IAM role or an external role defined as consumption role.

When processing a sharing task for an S3 Bucket, data.all will:
1. Update the S3 Bucket policy to add permissions to the principal IAM role
2. Create/Update the IAM policy "Share policy" that grants IAM permissions to the requested S3 bucket and KMS key. Attach this policy to the principal IAM role.
3. (If the Bucket is encrypted using a KMS key) Update the KMS Key policy to add permissions to the principal IAM role

### Glue Table sharing
In this type of share the permissions are granted to the IAM role specified in the request as principal. It 
can be either a data.all team IAM role or an external role defined as consumption role.

When processing a sharing task for a Glue Table, data.all will:
1. Create a Glue database in the target account with name of the original database plus the suffix `_shared`. This database will be re-used if other share requests for the same source databaser are processed for other principals in the same environment.
2. (If the share is cross-account) Revoke IAMAllowedPrincipal permissions from the table to ensure Lake Formation is used in the management of the table access and update LakeFormation to use Version 3 if not already >=3
3. Grant Lake Formation permissions on the original database and table to the IAM principals in the target. If the share is cross account this step will create a RAM invitation that data.all will identify and accept.
4. Create a resource link table from the original database table to the `_shared` database in the target account
5. Grant Lake Formation permissions to the resource link table for the IAM principals.

### S3 Prefix sharing (Folders)
In this type of share the permissions are granted to the IAM role specified in the request as principal. It 
can be either a data.all team IAM role or an external role defined as consumption role.

When processing a sharing task for a Folder, data.all will:
1. Update the Dataset Bucket policy to allow access point sharing. This is a one-time operation
2. Create/Update an S3 Access Point and its policy granting permissions to the requested S3 prefix (folder) in the bucket for the principal IAM role.
3. Create/Update the IAM policy "Share policy" that grants IAM permissions to the S3 Access Point and KMS key. Attach this policy to the principal IAM role.
4. (If the Bucket is encrypted using a KMS key) Update the KMS Key policy to add permissions to the principal IAM role

### Redshift Table sharing
In this type of share the permissions are granted to the Redshift role in the Redshift namespace specified in the request.

When processing a sharing task for a Redshift table, data.all will:
1. In the source namespace, create a Redshift datashare. Add requested schema and tables to the datashare.
2. Grant access to the datashare for the consumer namespace (same account) or for the consumer AWS account (cross account)
3. (If cross-account share) Authorize and associate datashare with the target namespace
4. In the target namespace, create local database for the datashare and grant permissions to the principal Redshift role.
5. In the target namespace, create external schema in local database and grant usage permissions to the principal Redshift role.
6. For the local database and for the external schema, grant select access to the requested table to the principal Redshift role.

## **Consume shared data**
Knowing what we know form the previous section we can now define some ways of consuming the shared data for each type of shareable item.

### S3 Bucket sharing
For S3 bucket sharing, IAM policies, S3 bucket policies, and KMS Key policies (if applicable) are updated to enable sharing of the S3 Bucket resource.
Therefore, we can use S3 API calls to access the data referring the Bucket directly. We need to assume or use the credentials
of the principal IAM role used in the share request (team IAM role or consumption IAM role).

Here is an example using the AWS CLI:

```json
 aws s3 ls s3://<BUCKET_NAME>
```

### Glue Table sharing

Glue tables are shared using AWS Lake Formation, therefore any service that reads Glue tables and integrates
with Lake Formation is able to consume the data.

We need to assume or use the credentials
of the principal IAM role used in the share request (team IAM role or consumption IAM role).

### S3 Prefix sharing (Folders)
For the case of folders, the underlying sharing mechanism used is S3 Access Points. You can read data inside a prefix 
executing API calls to the S3 access point.

We need to assume or use the credentials
of the principal IAM role used in the share request (team IAM role or consumption IAM role).

For example, we could use the AWS CLI with the following access point:
```json
 aws s3 ls arn:aws:s3:<SOURCE_REGION>:<SOURCE_AWSACCOUNTID>:accesspoint/<DATASETURI>-<REQUESTER-TEAM>/<FOLDER_NAME>/
```


### Redshift Table sharing

Redshift tables are shared through Redshift datashares and the principal of the share request is a Redshift role. Thus,
we can consume data accessing the Redshift Query editor or other applications that consume from Redshift with a user
that has access to the Redshift role. 


## **Email Notification on share requests**

In data.all, you can enable email notification to send emails to requesters and approvers of a share request. Email notifications 
are triggered during all share workflows - Share Submitted, Approved, Rejected, Revoked. 

The content sent in email notification is similar to the UI based notification. 

For example the email body will look like, 
```text
User <USERNAME> <SHARE_ACTION> share request for dataset <DATASET_NAME>

where <SHARE_ACTION> corresponds to "submitted", "approved", "revoked", "rejected"
```

**Note** - In order to enable email notification, you need to configure it in `config.json` and setup the AWS services 
needed for during the deployment phase. Please review steps for setting up email notification on <a href="https://awslabs.github.io/aws-dataall/">data.all</a> webpage
in the `Deploy to AWS` section


