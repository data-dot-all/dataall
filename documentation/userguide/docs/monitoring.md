# **Platform Monitoring**
As an administrator of data.all I want to know the status of data.all. In this section
we will focus on the following aspects of monitoring:

- Platform observability
- Platform usage

##  **Observability**
It refers to the infrastructure of data.all, the frontend and backend.

### AWS CloudWatch
As part of the deployment, data.all deploys observability AWS resources with CDK and ultimately in CloudFormation. 
These include AWS CloudWatch Alarms on the infrastructure: on Aurora DB, on the OpenSearch cluster, on API errors… 
Operation teams can subscribe to a topic on Amazon SNS to receive near real time alarms notifications when issues 
are occurring on the infrastructure.

### AWS CloudWatch RUM
Additionally, if we enabled CloudWatch RUM in the config.json file when we deployed data.all we 
will be able to collect and view client-side data about your web application performance from actual user 
sessions in near real time.

##  **Platform usage**
I want to know how my teams are using the platform.
Inside this category we answer questions such as *"how many environments or datasets are in data.all?"*.

### RDS Queries
The first option is to query the RDS metadata database that contains all the information regarding environments, datasets and other data.all objects.
You need access to the data.all infrastructure account, in which you will:
1) Navigate to RDS Console
2) Connect with secrets manager ARN
3) Get this ARN from AWS Systems Manager Parameter Store (search for "aurora")
4) Run SQL statements to extract insights about the usage of the platform


### Quicksight enabled monitoring
When we deployed data.all, we can configure optional monitoring of Quicksight, this is the `enable_quicksight_monitoring` parameter.
If enabled, we allow AWS Quicksight to establish a VPC connection with our RDS metadata database in that account.
We modify the security group of our Aurora RDS database to communicate with Quicksight, then we can use AWS Quicksight to 
create rich dynamic analyses and dashboards based on the information on RDS. Once the deployment is complete you need to follow the next steps:

**1) Pre-requisite: Quicksight Enterprise Edition**
We need to subscribe to Quicksight and allow data.all domain to embed dashboards, follow the instructions in the step 4 of the
<a href="environments.html#link-environment">Linking environment section</a>. 


**2) Create Quicksight VPC connection**

Follow the steps in the
<a href="https://docs.aws.amazon.com/quicksight/latest/user/vpc-creating-a-connection-in-quicksight.html">documentation</a>
 and make sure that you are in the same region as the infrastructure of data.all. For example, in this case Ireland region.

![quicksight](pictures/monitoring/vpc1.png#zoom#shadow)

To complete the set-up you will need the following information:

- VPC_ID of the RDS Aurora database, which you can find in the RDS Console

![quicksight](pictures/monitoring/vpc1.png#zoom#shadow)

- Security group created for Quicksight: In the VPC console, under security groups, look for a group called `<resource-prefix>-<envname>-quicksight-monitoring-sg`
For example using the default resource prefix, in an environment called prod, look for `dataall-prod-quicksight-monitoring-sg`.

**3) [WIP] Create Aurora data source and Quicksight data sets**
We have automated this step for you! As a tenant user, a user that belongs to `DAADministrators` group, sign in to data.all.
In the UI navigate to the **Admin Settings** window by clicking in the top-right corner. You will appear in a window with 2 tabs: Teams and Monitoring.
In the Monitoring tab, introduce the VPC connection ... and click on .....


**4) Customize your analyses and share your dashboards**
Explore Quicksight documentation for next steps, such as <a href="https://docs.aws.amazon.com/quicksight/latest/user/working-with-visuals.html">customization of analyses</a>,
<a href="https://docs.aws.amazon.com/quicksight/latest/user/share-dashboard-view.html">sharing dashboards</a>
or <a href="https://docs.aws.amazon.com/quicksight/latest/user/sending-reports.html">sending reports via email</a>.

!!! abstract "Not only RDS"
    With Quicksight you can go one step further and communicate with other AWS services and data sources. Explore the documentation
    for cost analyses in AWS with Quicksight or AWS CloudWatch Logs collection and visualization with Quicksight.




