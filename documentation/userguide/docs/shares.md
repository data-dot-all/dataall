# **Shares**
Teams can browse data.all catalog and request access for data assets.
data.all shares data between teams securely within and environment and across environments without any data movement.


Datasets can contain tables and folders. Tables are Glue Tables registered in Glue Catalog.
data.all uses (and automates)
<a href="https://docs.aws.amazon.com/lake-formation/latest/dg/sharing-catalog-resources.html" target="_blank">Lake Formation sharing feature</a>
to create access permissions to tables, meaning that no data is copied between  AWS accounts.

Under-the-hood, folders are prefixes inside the dataset S3 bucket. To create sharing of folders in data.all,
we create an S3 access point per requester group to handle its access to specific prefixes in the dataset.

data.all also supports the sharing of the entire S3 Bucket to requestors using IAM permissions and S3/KMS policies if desired.

**Concepts**

- Share request or Share Object: one for each dataset and requester team.
- Share Item refers to the individual tables and folders or S3 Bucket that are added to the Share request.

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


### **Create a share request (requester)**

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

## **Approve/Reject a share request (approver)**

As an approver, click on **Learn more** in the `SUBMITTED` request and in the share view you can check the tables and folders added in the request.
This is the view that approvers see, it now contains buttons to approve or reject the request.

![submit_share_2](pictures/shares/shares_submitted.png#zoom#shadow)

If the approvers **approve** the request, it moves to the `APPROVED` status. Share items IN `PENDINGAPPROVAL` will go to `SHARE_APPROVED`. 

![accept_share](pictures/shares/shares_approved.png#zoom#shadow)

Data.all backend starts a sharing task, during which, items and the request
are in `SHARE_IN_PROGRESS` state. 

![accept_share](pictures/shares/shares_in_progress.png#zoom#shadow)

When the task is completed, the items go to `SHARE_SUCCEEDED` or `SHARE_FAILED` and the request is `PROCESSED`.

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

For S3 bucket sharing, IAM policies, S3 bucket policies, and KMS Key policies (if applicable) are updated to enable sharing of the S3 Bucket resource.

For example, access to the bucket would be similar to:
```json
 aws s3 ls s3://<BUCKET_NAME>
```

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

