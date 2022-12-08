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
the request. Then requesters submit it and wait until approvers pick it up from the `PENDING APPROVAL` and approve or
reject the request which will go to `APPROVED` or `REJECTED` status correspondingly. If at a later state an approved
share needs to be rejected, approvers can revoke access. Finally, approvers and requesters can always edit the share
request which will send it back to a `DRAFT` state.


![wf](pictures/shares/share_wf.png#zoom#shadow)

### **Create a share request to a table (requester)**

On left pane choose **Catalog** then **Search** for the table you want to access. Click on the lock icon of the selected
data asset.

![catalog_search](pictures/shares/shares_1.png#zoom#shadow)

The following window will open. Choose your target environment and team and optionally add a *Request purpose*.

![share_request_form](pictures/shares/share_2_1.png#zoom#shadow)

If instead of to a team, you want to request access for a Consumption role, add it to the request as in the picture below.

![share_request_form](pictures/shares/share_2_2.png#zoom#shadow)

Finally,
click on **Send Request**. This will create a share request or object for the corresponding dataset
and if you have requested a table or folder
it will add those items to the request. The share needs to be submitted for the request to be sent to the approvers.

### **Submit a share request (requester)**
A created share request needs to be filled with requested tables and/or folders and then submitted. For the previous
example, where we requested access to a table directly from the share request form, the requester can click on
**Submit** from the Shares menu on the *Sent* tab.

![submit_share_2](pictures/shares/shares_3.png#zoom#shadow)

If we have created a share request for a dataset or we want to edit the tables and folders that we want to access to,
select **Learn more** to open the request. Is *supermarket_sales* the only table you want to get access to? yes?
then click on **Submit** and wait for the approver to approve or reject the share request.


### **Approve/Reject a share request (approver)**
!!! success "Notifications"
    When a share request is submitted, the approvers receive a notification with the user that is requesting access
    and the dataset. And viceversa, when a request is approved, the requesters get a notification with the
    approver's name and the approved dataset.
shares
As a dataset **owner** or **steward** you can approve or reject a dataset access request. To do that, you have 2 options.
First, you can go from the Shares menu and in the *Received* tab approve or reject the request that is pending approval.

If you want to check the content of the request before approving or rejecting, click on **Learn more** and the
following will open. Here you can see the tables and folders added to the dataset share request.

![accept_share](pictures/shares/shares_5.png#zoom#shadow)

If a dataset share request has been accepted, the requester should see the dataset on his or her screen. The role with
regards to the dataset is `SHARED`.


### **Add/delete items to/from a share request (requester/approver)**
When you create a share request for a dataset, you still need to add the items (tables or folders) that you want to
get access to. Or if you have an existing share request with some shared tables and folders, you can add more items
to the request or delete shared ones.

It will be more clear with an example. As appears in the picture, go to the share request and click on **Add Item**
to add a table or folder to the request. On the contrary, if you want to remove a shared item click on the trash icon
next to it.


If you are adding a new item to the request, the following window will open to let you choose a specific table
or folder in the dataset.

![add_share](pictures/shares/shares_6.png#zoom#shadow)

!!! warning "**You have to submit the request again!!**"
    Note that after you have added or removed an item, the share request status has gone from `APPROVED` to `DRAFT`.
    Since the request has changed it needs to be resubmitted. **Both, approvers and requesters, can add or delete items
    from a share request, but ONLY requesters can submit the new draft of the request.** So after adding or deleting
    items requesters have to follow the steps for resubmitting explain above.



### **Revoke a share request (approver)**
What happens if you granted access (you are an approver)
to a dataset/tables/folders and now you want to revoke that access? In case you made
a mistake, or your data cannot be shared any longer; go to the Shares menu and look for the specific share request
in the *Received* tab. In the top right corner there is a **Revoke** button that will behave as a rejection of a
pending approval share request. In fact the status of the request changes to `REJECTED`.


## **Check your sent/received share requests**
Anyone can go to the **Shares** menu on the left side pane and look up the share requests that they have received
and that they have sent.


## **Consume shared data**
Data.all tables are Glue tables shared using AWS Lake Formation, therefore any service that reads Glue tables and integrates
with Lake Formation is able to consume the data. Permissions are granted to the team role or the consumption role that 
has been specified in the request.

For the case of folders, the underlying sharing mechanism used is S3 Access Points. You can read data inside a prefix using 
the IAM role of the requester (same as with tables) and executing get calls to the S3 access point.

### **Use data subscriptions**
data.all helps data owners publish notification updates to all their data consumers.
It also helps data consumers react to new data shared by the owners.

#### Step 1: Enable subscriptions on the environment

Check the <a href="environments.html">environment</a> documentation for the steps to enable subscriptions.

!!!abstract "AWS SNS Topics"
    When subscriptions are enabled, **as a data producer you can publish a message** to the producers SNS topic.
    You can also **subscribe to data consumers SNS topic** to be aware of the latest data updates from the producers.

#### Step 2: Publish notification update
**IMPORTANT**

This feature is disabled at the moment

