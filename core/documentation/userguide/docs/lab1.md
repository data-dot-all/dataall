# **Hands-on Lab: Data Access Management with data.all teams**

This document is a step-by-step guide illustrating some functionalities
of the data.all "Teams" feature. This guide is far from exhaustive and
mainly focuses on how users can share data across environment and teams.
After completing it, you are free to continue exploring data.all and the
functionalities it provides.

## 🎯 **Scope of this guide**


To follow this guide, you will need:

-   An AWS account (#111111111111) where data.all is deployed. Your
    version of data.all must support the "Teams" feature

-   An AWS account that will be used as a data.all environment for the
    data platform team (#222222222222)

-   An AWS account that will be used as a data.all environment for the
    data science team (#333333333333)

The scenario you will implement in this guide is the following. The data
platform team owns a dataset. Data scientists are interested by the
content of this dataset for their analysis. There are however two
different types of data scientists, that are members of two different
teams: data science team A and data science team B.

A data scientist from team A will request access to the data platform
dataset for its team. A data platform user will then accept the request,
thus granting team A read-only access to the dataset. Team B does not
have access to the dataset from the data platform team.

Then a user in team A creates a dataset in the data science environment.
We will check that users in team B does not have access to this data.

You will go through the following steps to implement this scenario:

1.  Create users and groups in Cognito

2.  Create the Organisation and the Environment for the data platform
    team

3.  Create the Dataset for the data platform team and upload some data

4.  Create the Organisation and the Environment for the data science
    team

5.  Invite team A and team B to the data science environment

6.  Share data platform data with team A in the data science environment

7.  Create a Dataset managed by team A in the data science account

Here is an illustration of the scenario:



### **1. Create users and groups in Cognito**


First, you need to create users and groups from the Cognito console.
This happens in the account where the infrastructure of data.all is
deployed (#111111111111). You will later use these users to connect to
data.all. Go to the AWS console and create five groups and four users as
follow:

**Cognito group**



-   **DAAdministrators**: group for data.all administrators

-   **DataPlatformaAdmin**: group for data platform admin team

-   **DataScienceAdmin**: group for data science admin team

-   **TeamA**: first category of data scientists

-   **TeamB**: second category of data scientists

**Cognito users**



-   **data.alladmin**: create this user and add it to both in the
    DAAdministrators and DataPlatformAdmin groups. This user will be
    able to manage permissions of all teams in data.all (tanks to the
    DAAdministrators group membership) and will be able to create
    resources for the data platform team

-   **ds-admin**: create this user and add it to the DataScienceAdmin
    group. This user will create resources for the data science team

-   **ds-a**: create this user and add it to TeamA

-   **ds-b**: create this user and add it to TeamB

!!! warning "Warning"
    When creating users, you will need to **provide both the name of the user and its email.**

After creating users and assigning them to groups in Cogntio, you end-up
with the following situation:



### **2. Create the Organisation and the Environment for the data platform team**

We will start by creating the resources for the data platform team. Log
into data.all with the user in the **DataPlatformAdmin** group. Create an
Organisation for the Data Platform team. Make sure that the
DataPlatformAdmin team manages this organization.




Now link a new environment to this organisation. You can do this by
clicking on **Environment** and then **Link Environment**




When onboarding a new AWS account as an environment in data.all, you
usually need to make some operations in the account first. The UI lists
these operations for you: bootstrapping the AWS account and creating the
data.allPivotRole notably. You will have to go through these operations
if it is the first time you use this AWS account to create an
environment in data.all. Then, create the environment by providing a
name, the account ID (#**222222222222**) and the Team managing it
(**DataPlatformAdmin**).




Wait until the stack is deployed successfully. You can check the status
of the stack in the **stack** tab of the environment. Once the status is
**create_complete**, create a new dataset in this environment. You can
do it from the **Contribute** window


Deploy this dataset in the environment you have just created. Also make
sure that the **DataPlatformAdmin** team owns this dataset (Governance
section):



Wait until the dataset is created successfully. You can check the status
in the **stack** tab of the dataset. Once the status is
**create_complete**, you can start uploading some data from the
**upload** tab:



From this window, you are able to upload files in your dataset. When
uploading files, you can ask for a crawler running automatingly in your
dataset, thus populating a glue database. To make sure the crawler will
work, please upload a csv file of your choice. Insert any name you want
in the **prefix** section. This will be the name of your Glue table.



Click on the **upload** button. This puts your file in the S3 bucket
related to your data.all dataset. It also launches the Glue crawler
populating the Glue database. Leave some time for the crawler to run and
click on the **Tables** tab. If the crawler ran successfully, clicking
on the **synchronize** button will display your table. At this point,
feel free to explore your table from the data.all user interface.



We have completed all the tasks on the data platform side. This included
the creation of the organisation, the environment, the dataset and the
upload of a csv file. This is an illustration of where we are in the
process:




**Note**: As you may have already noted down at the beginning of
this guide, the data platform user is also part of the
**DAAdministrators** group. Being part of this group enables this user
to manage the permissions of all the other teams in data.all. To do so,
click **Setting**. This provides the list of teams for which you can
manage the permissions.



Click on the icon next to the team's name to manage its permissions



This opens a new window from where you can manage all permissions of the
team.



### **3. Create the Organisation and the Environment for the data science team**

You will now create data.all resources for the data science team. Log
into data.all with the user in the **DataScienceAdmin** group. Create an
Organisation for the data science team. Make sure that the
**DataScienceAdmin** team manages this organization.



Now link a new environment to this organisation. Provide a name for this
environment, the AWS account ID (**#333333333333**), and the team owning
it (**DataScienceAdmin**).



You now have an organisation and an environment managed by the
**DataScienceAdmin** team. The next step is to invite team A and team B
to this data science environment. This will enable data scientists from
team A and team B to access the environment.

### **4. Invite Team A and Team B to the data science environment**

With the user in DataScienceAdmin team, select the data science
environment and click on the **Teams** tab. You can invite other teams
in your environment with the **invite** button.



This opens a new window asking you to indicate the name of the team you
want to invite. You can also manage the permissions this team will have
in your environment. Use this **invite** button to invite **TeamA** and
**TeamB** in your data science environment.



Users from team A and team B now have access to your environment

### **5. Share data platform data with Team A in the data science environment**

Log into data.all with user in **TeamA**. This user does not own any
data, but wants to access data of the data platform team. Go on data.all
**Data Catalog** tab. This shows all the datasets and tables you can
request access to. There are different tools you can use in order to
find the data you are looking for (you can find more information about
these in the data.all documentation):

-   Directly typing the name of the dataset or the table in the search
    bar

-   Use tags or topics associated to the datasets

-   Use data.all Glossary

In this case, data scientist in team A wants to access **mydpdata**
uploaded by the data platform team. Use the search bar to find the data.
When you see the table you want, click on **Request access**.



This button opens a new window where you can configure your request.
When you share a dataset or a table in data.all, the share occurs at an
environment and team level. You therefore need to indicate for which
environment and for which team you make the request. In this case, the
user in team A wants to access data in the data science environment.
Fill the request accordingly.



When you click on **Send Request**, this does not directly send the
request to the data latform team. It rather creates a Draft that you can
still edit in the **Collaborate** tab, under **Sent**. Click on the
**Submit** button to send the request



Now re-open a new data.all window connected as the user in the
**DataPlatformAdmin** team. This team owns the dataset and is therefore
responsible of accepting access requests. It is possible to delegate
this right to other teams using **Data Stewards** but we did not set
this up in this guide. Under **Collaborate** and **Received**, you can
find all the access requests received by the data platform team. Locate
the request you just made with the user in Team A. If you want to know
more about this request (who is making it, for which table in the
dataset,...), click on **Learn More**. If you agree to grant access,
click on **Approve**.



This action triggers an ECS task that updates the permissions of the
table in Lake Formation. Users in Team A are now able to access the data
platform data. Let us verify it.

Re-open data.all connected as the user in **TeamA**. You can first visit
the **Contribute** tab where you will see the dataset that has been
shared with team A.



**Quick reminder**: The data platform team agreed to share the
**mydpdata** table with TeamA in the data science environment called
**DSENV**.

As a conclusion, the table **mydpdata** is accessible from the
environment **DSENV**, through a role only team A can assume. Team A
users can assume this role directly from the data.all user interface.
Select the data science environment and go under the **Teams** tab. You
will then see all the teams that have access to the environment. Find
TeamA line and click on the AWS logo.



This opens a new window in the AWS console. The AWS account is the one
you associated to the data science environment earlier in this guide
(#333333333333). Also note that you are assuming a role specific to your
team. Use the search bar to get to the Athena console. In the Athena
Query editor, you will be able to see under **Database** the dataset
shared by the data platform team. The name of this database is a
concatenation of "dh" (for data.all), the name of the dataset (dpdataset)
and random characters to ensure unicity. Under **Tables**, you can now
see **mydpdata** which you can query using with Athena.



**Explanation**: When the data platform team uploaded the csv file
under the **mydpdata** prefix, the crawler created a new Glue table
called **mydpdata** in the AWS account associated to the data platform
environment (#333333333333). When the data platform team accepted to
share **mydpdata** with team A in the data science environment, it
triggered an ECS task that updated the Lake Formation (AWS service
managing data access) settings in both the data platform and data
science environments. It updated the settings in a way that allows the
IAM role of team A in the data science environment to read the
**mydpdata** table stored in the data platform environment. In short,
only the role of team A in the data science environment is able to read
**mydpdata** table (in addition to data platform team of course). This
is a **read-only** access, and the data is not moved from the data
platform environment to the data science environment.

You can repeat the same thing to check that team B does not have access
to the data. Log into data.all with a user in **TeamB** and select the
data science environment. Under the **Teams** tab, click on the AWS logo
to connect to the AWS console assuming the role of **TeamB**. Go to the
Athena Query Editor and you will see that you won't be able to see data
shared with team A.

At this stage of the guide, you should better understand how data
sharing cross account works. The graph below illustrates where we are in
the original scenario.


### **6. Create a Dataset managed by team A in the data science account**

In the previous section of this guide, you went through an example of
how you can share data across environment and teams. In this section, we
will focus on the creation of datasets in a single account. Team A will
create a dataset in the data science environment. We will make sure that
other teams invited to the data science environment (t eamB) are not
able to access the dataset of team A.



Open data.all with a user in **TeamA**. In the **Contribute** section,
create a new dataset in the data science environment. Make sure that
**TeamA** owns this dataset.



When the dataset is fully created, upload a csv file from the **upload**
tab of the dataset. Upload this file under a prefix named **datateama**
to create a new Glue table with the same name. After uploading the file,
wait a few minutes to let the crawler do its job. In the **Tables**
section, click on **Synchronize** to display your new table.



Now that the data is uploaded, team A is able to access the data as it
is registered as the owner of the dataset. However, team B is not able
to read the data even if it has access to the environment. If you log
into data.all with the user in team B, you won't be able to see the
**TeamADataset** in the **Contribute** section. In addition, you will
find below two screenshot of the Athena console. In the first
screenshot, we assume the role of **TeamA** in the data science
environment (process already explained in the previous section). In the
second screenshot, we assume the role of **TeamB** in the data science
environment. When assuming the role of team A, we can see the team A
dataset in the **database** section, and also the **datateama** table.
We can then query the data with Athena. However, when assuming the role
of team B in the data science environment, we are not able to see any
dataset. This is because in this guide, we have not created or shared
any dataset with team B. Team B is thus unable to query the data of team
A.




This last section illustrated how you can use teams to manage data
access in a single environment. You have reached the end of the guide
that illustrated some capabilities that data.all brings. Now that you got
the basis, fell free to explore all the other things you can do with
your data.

### **Cleanup**

When you are done with this guide, you delete your data.all resources
(dataset, environment, organization). This also automatically deletes
the Cloudformation stacks created in your AWS accounts.
