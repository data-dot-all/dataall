# **Environments and Teams**

An environment is a **workplace** where a team can bring, process, analyze data and build data driven applications.
Environments comprise AWS resources, thus when we create an environment, we deploy a CDK/CloudFormation stack
to an AWS account and region. In other words, **an environment is mapped to an AWS account in one region, where
users store data and work with data.**

!!! danger "One AWS account, One environment"
    To ensure correct data access and AWS resources isolation, onboard one environment in each AWS account.
    **We strongly discourage users to use the same AWS account for multiple environments**.

## :material-hammer-screwdriver: **AWS account Pre-requisites**
*data.all* does not create AWS accounts. You need to provide an AWS account and complete the following bootstraping
steps. Only the first step, CDK bootstrap, is mandatory; the rest are needed depending on your deployment configuration
or on the features enabled in the environment.

### 1. CDK Bootstrap

<span style="color:grey">*data.all*</span> uses AWS CDK to deploy and manage resources on your AWS account.
AWS CDK requires some resources to exist on the AWS account, and provides a command called `bootstrap` to deploy these
specific resources in a particular AWS region.

In this step we establish a trust relationship between the data.all infrastructure account and the accounts to be linked as environments.
data.all codebase and CI/CD resources are in the data.all **tooling account**,
and all the application resources used by the platform
are located in a **infrastructure account**. From the infrastructure account we will deploy environments and other resources
inside each of our business accounts. We are granting permissions to the infrastructure account 
by setting the `--trust` parameter in the cdk bootstrap command.

To boostrap the AWS account using AWS CDK, you need the following (which are already fulfilled if you open AWS CloudShell from the environment account).

1. to have AWS credentials configured in ~/.aws/credentials or as environment variables.
2. to install cdk: `npm install -g aws-cdk`

Then, you can copy/paste the following command from the UI and run from your local machine or CloudShell:
````bash
cdk bootstrap --trust DATA.ALL_AWS_ACCOUNT_NUMBER  -c @aws-cdk/core:newStyleStackSynthesis=true --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess aws://YOUR_ENVIRONMENT_AWS_ACCOUNT_NUMBER/ENVIRONMENT_REGION
````


!!! note "Which account should I put in the command?"
    Let's check with an example: the **tooling account** is 111111111111 and data.all was deployed to
    the **infrastructure account** = 222222222222. Now we want to onboard a **business account**
    = 333333333333 in region eu-west-1. Then the cdk bootstrap command will look like:
    ````bash
    cdk bootstrap --trust 222222222222  -c @aws-cdk/core:newStyleStackSynthesis=true --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess aws://333333333333/eu-west-1
    ````

!!! danger "After deleting an environment it is strongly recommended to untrust data.all infrastructure account. Read more [here](#delete-an-environment)" 

#### Restricted CDK Execution role
In the above command we define the `--cloudformation-execution-policies` to use the AdministratorAccess policy `arn:aws:iam::aws:policy/AdministratorAccess`. 
This is the default policy that CDK uses to deploy resources, nevertheless it is possible to restrict it to any IAM policy created in the account.

A more restricted policy named `DataAllCustomCDKPolicyREGION` is provided and directly downloadable from the UI. This more restrictive 
policy can be optionally passed in to the parameter `--cloudformation-execution-policies` instead of `arn:aws:iam::aws:policy/AdministratorAccess` for the CDK Execution role.

````bash
aws cloudformation --region REGION create-stack --stack-name DataAllCustomCDKExecPolicyStack --template-body file://cdkExecPolicy.yaml --parameters ParameterKey=EnvironmentResourcePrefix,ParameterValue=dataall --capabilities CAPABILITY_NAMED_IAM && aws cloudformation wait stack-create-complete --stack-name DataAllCustomCDKExecPolicyStack --region REGION && cdk bootstrap --trust 225091619433 -c @aws-cdk/core:newStyleStackSynthesis=true --cloudformation-execution-policies arn:aws:iam::ACCOUNT_ID:policy/DataAllCustomCDKPolicyREGION aws://ACCOUNT_ID/REGION
````

#### Environments in multiple regions
v2.4.0 allows the creation of multiple environments in the same AWS account and in multiple regions. We need to bootstrap every
region that will host an environment. 

!!! note "Regional CDK Execution Policy"
    Every CDK execution role requires its own `DataAllCustomCDKPolicyREGION` IAM policy. If you are using restricted
    CDK execution roles you need a different `DataAllCustomCDKExecPolicyStack` for each region used.


### 2. (For manual) Pivot role
<span style="color:grey">*data.all*</span> assumes a certain IAM role to be able to call AWS SDK APIs on your account. 
The Pivot Role is a super role in the environment account and thus, it is 
protected to be assumed only by the data.all central account using an external Id.

Since release V1.5.0, the Pivot Role can be created as part of the environment CDK stack, given that the trust between data.all and the environment account
is already explicitly granted in the bootstraping of the account. To enable the creation of Pivot Roles as part
of the environment stack, the `cdk.json` parameter `enable_pivot_role_auto_create` needs to be set to `true`. 
When an environment is linked to data.all a nested stack creates a role called **dataallPivotRole-cdk**.

For versions prior to V1.5.0 or if `enable_pivot_role_auto_create` is `false` the Pivot Role needs to be created manually.
In this case, the AWS CloudFormation stack of the role can be downloaded from <span style="color:grey">*data.all*</span> environment creation form. 
(Navigate to an organization and click on link an environment to see this form). Fill the CloudFormation stack with the parameters
available in data.all UI to create the role named **dataallPivotRole**. 

!!! success "Upgrading from manual to cdk-created Pivot Role"
    If you have existing environments that were linked to data.all using a manually created Pivot Role you can
    still benefit from V1.5.0 `enable_pivot_role_auto_create` feature. You just need to update that parameter in
    the `cdk.json` configuration of your deployment. Once the CICD pipeline has completed: new linked environments 
    will contain the nested cdk-pivotRole stack (no actions needed) and existing environments can be updated by:
      <br>a) manually, by clicking on "update stack" in the environment --> stack tab
      <br>b) automatically, wait for the `stack-updater` ECS task that runs daily overnight 
      <br>c) automatically, set the added `enable_update_dataall_stacks_in_cicd_pipeline` parameter to `true` in the `cdk.json` config file. The `stack-updater` ECS task will be triggered from the CICD pipeline


### 3. (For Dashboards) Subscribe to Amazon Quicksight

This is an optional step. To link environments with <i><b>Dashboards enabled</b></i> , you will also need a running Amazon QuickSight subscription
on the bootstraped account. If you have not subscribed to Quicksight before, go to your AWS account and choose the
Enterprise option as show below:

![quicksight](pictures/environments/boot_qs_1.png#zoom#shadow)

![quicksight](pictures/environments/boot_qs_2.png#zoom#shadow)


### 4. (For ML Studio) Specifying a VPC or using default
If ML Studio is enabled, data.all will create a new SageMaker Studio domain in your AWS Account and use the domain later on to create ML Studio profiles.

Prior to V1.5.0 data.all always used the default VPC to create a new SageMaker domain. The default VPC had then to be
customized to fulfill the networking requirements specified in the Sagemaker
[documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-notebooks-and-internet-access.html) for VPCOnly 
domains.

In V1.5.0 we introduce the creation of a suitable VPC for SageMaker as part of the environment stack. However, it is not possible to edit the VPC used by a SageMaker Studio domain, it requires deletion and re-creation. To allow backwards
compatibility and not delete the pre-existing domains, in V1.5.0 the default behavior is still to use the default VPC.

In V2.2.0, we introduced the ability to select your own VPC ID and Subnet IDs to deploy the VPC-Only Sagemaker Studio domain to.

Data.all will follow the following rules to establish which VPC to use for Sagemaker Studio domain creation:

- If MLStudio enabled with VPC and subnet IDs specified
  - Use the specified VPC and subnet IDs
- If MLStudio enabled with no VPC/subnet IDs specified 
  - default VPC exists -->  Uses default VPC and all subnets available
  - default VPC does not exist --> Creates a new VPC and uses with private subnets

Pre-existing environments from older versions of data.all will have their Sagemaker Studio domain remain unchanged if already enabled. Users can get a better understanding of what VPC configuration is being used by navigating to the environment --> MLStudio Tab in the data.all UI once the environment stack is created.


## :material-new-box: **Link an environment**
### Necessary permissions
!!! note "Environment permissions"
    Only organization Administrator teams can link environments to the Organization. The Organization creator team is
    the by default Organization Administrator team, but users of this group can now invite other teams and grant them
    permission to manage organization teams, and link environment to the organization.

Managing organization teams can be done through the UI or APIs. From the UI, navigate to your organizations and
click on the **Teams** tab.

![](pictures/environments/org_invite_group_1.png#zoom#shadow)

Invite button opens a dialog that gives the organization creators the
possibility to invite one of the IdP groups they belong to, which will appear in a dropdown when we click on **Teams**.
They can also invite an IdP group that they don't belong to, as long as they type the exact group name (**case
sensitive**):

![](pictures/environments/org_invite_group_2.png#zoom#shadow)

You can check the Organization administrators teams in the Organization's **Teams** tabs and remove a team if
necessary on the icon in the Actions column.


![](pictures/environments/org_invite_group_3.png#zoom#shadow)

### Link environment
Once the AWS account/region is bootstraped and we have permission to link an environment to an organization, let's go!
Navigate to your organization, click on the **Link Environment** button, and fill the environment creation form:

![](pictures/environments/env_link_1.png#zoom#shadow)


| Field             | Description                                                                                                                               | Required | Editable |Example
|-------------------|-------------------------------------------------------------------------------------------------------------------------------------------|----------|----------|-------------
| Environment name  | Name of the environment                                                                                                                   | Yes      | Yes      |Finance
| Short description | Short description about the environment                                                                                                   | No       | Yes      |Finance department teams
| Account number    | AWS bootstraped account maped to the environment                                                                                          | Yes      | No       |111111111111
| Region            | AWS region                                                                                                                                | Yes      | No       |Europe (Ireland)
| IAM Role ARN     | Alternative name of the environment IAM role                                                                                              | No       | No       |anotherRoleName
| Resources prefix  | Prefix for all AWS resources created in this environment. Only (^[a-z-]*$)                                                                | Yes      | Yes      |fin
| Team              | Name of the group initially assigned to this environment                                                                                  | Yes      | No       |FinancesAdmin
| Tags              | Tags that can later be used in the Catalog                                                                                                | Yes      | Yes      |finance, test
| ML Studio VPC ID    | VPC to host the environment sagemaker studio domain (if mlstudio is enabled) instead than the default VPC or the VPC created by <span style="color:grey">*data.all*</span>         | No       |   No       | vpc-......
| ML Studio Subnet ID(s)   | Subnet(s) to host the environment sagemaker studio domain (if mlstudio is enabled) instead than the default subnets or the subnets created by <span style="color:grey">*data.all*</span>  | No       |  No        | subnet-....


**Features Management**

An environment is defined as a workspace and in this workspace we can flexibly activate or deactivate different
features, adapting the workspace to the teams' needs. If you want to use Dashboards, you need to complete the optional
third step explained in the previous chapter "Bootstrap your AWS account".

!!! success "This is not set in stone!"
    Don't worry if you change your mind, features are editable. You can always update
    the environment to enable or disable a feature.

Click on Save, the new Environment should be displayed in the Environments section of the left side pane.


## :material-card-search-outline: **Manage your Environment**
Go to the environment you want to check. You can find your environment in the Environments list clicking on the left
side pane or by navigating to
the environment organization. There are several tabs just below the environment name:

- Overview: summary of environment information and AWS console and credential access.
- Teams: list of all teams onboarded to this environment.
- Datasets: list of all datasets owned and shared with for this environment
- MLStudio: summary of Sagemaker Studio domain configuration (if enabled)
- Networks: VPCs created and owned by the environment
- Subscriptions: SNS topic subscriptions enabled or disabled in the environment
- Tags: editable key-value tags
- Stack: CloudFormation stack details and logs

!!! note "Environment access"
    If **none** of the teams you belong to (IdP groups) has been onboarded to the environment, you won't be able to see
    the environment in the
    environments menu or in the organization environments list. **Check the "Manage teams" section**

### :material-cloud-check-outline: **Check CloudFormation stack**
After linking an environment we can check the deployment of AWS resources in CloudFormation, click on the environment
and then on the **Stack** tab. Right after linking an environment you should find something like the below picture.

![](pictures/environments/env_tabs_1.png#zoom#shadow)

After some minutes its status should go from "PENDING" to "CREATE_COMPLETE" and we will be able to look up the
AWS resources created as part of the environment CloudFormation stack. Moreover, we
can manually trigger the update in case of change sets of the CloudFormation stack with the **Update** button.
!!! success "Pro Tip"
    If something in the creation or update of an environment fails, we can directly check the logs by clicking the logs button.
    No need to navigate to the AWS console to find your logs!

After being processed (not in `PENDING`), the status of the CloudFormation stack is directly read from
 <a href="https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-describing-stacks.html">CloudFormation</a>.

### :material-pencil-outline: **Edit and update an environment**
Find your environment in the Environments list or by navigating to the corresponding organization. Once in your selected
environment, click on **Edit** in the top-right corner of the window and make all the changes you want.

Finally, click on **Save** at the bottom-right side of the page to update the environment.
!!! success "Automatically updates the CloudFormation stack"
    Clicking on Save will update the environment metadata as well as the CloudFormation stack on the AWS account

### :material-trash-can-outline: **Delete an environment**
In the chosen environment, next to the Edit button, click on the **Delete** button.

!!! danger "orphan <span style="color:grey">*data.all*</span> resources"
    A message like this one: *"Remove all environment related objects before proceeding with the deletion!"* appears in
    the delete display. Don't ignore it! Before deleting an environment, clean it up: delete its datasets and other
    resources.

!!! danger "Untrust <span style="color:grey">*data.all*</span> infrastructure account"
    A message like this one: *"After removal users must untrust the data.all account manually from env account CDKToolkit stack!"* appears in
    the delete display. Don't ignore it!
    When you [boostrapped](#1-cdk-bootstrap) the environment account you explicitly "trusted" (using the `--trust <account id>` flag) the infrastructure
    account to make deployments to your account.
        
    * If you don't want to make CDK deployments (not necesserily related to data.all) to that account/region you can completely remove the CDKToolkit stack from CFN
        
    * If you want to continue using the account/region for other CDK deployments you must untrust the data.all account by rerunning `cdk bootstrap --trust <TRUSTED_NON_DATAALL_ACC1> --trust <TRUSTED_NON_DATAALL_ACC2> ...`

Note that we can keep the environment CloudFormation stack. What is this for? This is useful in case you want to keep
using the environment resources (IAM roles, etc) created by <span style="color:grey">*data.all*</span> but outside of <span style="color:grey">*data.all*</span>

### :material-plus-network-outline: **Create networks**
Networks are pre-existing VPCs that are onboarded to <span style="color:grey">*data.all*</span> and belonging to an environment and team. To create a network, click in the
**Networks** tab in the environment window, then click on **Add** and finally fill the following form.

!!!abstract "Using Networks"
    After onboarding your network(s) in <span style="color:grey">*data.all*</span>, users can easily select the VPC and Subnet information of that network to seamlessly deploy new resources in data.all that require VPC configurations, such as data.all Notebooks. For example, if a User wants to create a notebook in their environment after onboarding a network, the VPC and Subnet ID fields in the create notebook form on data.all will auto-populate with the VPC and subnet information for the user to easily to select (rather than navigating to and from the AWS Console)!


![](pictures/environments/env_networks.png#zoom#shadow)


### :material-tag-remove-outline: **Create Key-value tags**
In the **Tags** tab of the environment window, we can create key-value tags. These tags are not <span style="color:grey">*data.all*</span> tags
that are used to tag datasets and find them in the catalog. In this case we are creating AWS tags as part of the
environment CloudFormation stack. There are multiple tagging strategies as explained in the
<a href="https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html">documentation</a>.



## :material-account-plus-outline: **Manage Teams**

Environment creators have all permissions on the environment,
and can invite other teams to the onboarded environment. To add an IdP group to an environment, navigate to the
**Teams** tab of the environment and click on the **Invite** button.

![](pictures/environments/env_teams_1.png#zoom#shadow)

A display will allow you to customize the
AWS permissions that the onboarded group will have, adapting to different types of users
(data scientists, data engineers, data analysts, management). The customizable permissions can be enabled or
disabled as appears in the following picture.

![](pictures/environments/env_teams_2.png#zoom#shadow)

When the invitation is saved, the environment CloudFormation stack gets automatically updated and creates a
new IAM role for the new team. The IAM role policies are mapped to the permissions and are granted to the invited team
(e.g., a team  invited without "Create ML Studio" permission will not have
Sagemaker permissions on the associated IAM role).To remove a group, in the *Actions* column select the minus icon.


!!! warning "Automated permission assignment"
    Groups retrieved from the IdP are automatically granted all
    application high level permissions by default to accelerate the
    onboarding process.

Users will only be able to see the environments where a team that they belong to has been onboarded (either as
creator of the environment or invited to the environment). In the following picture, John belongs to the
*DataScienceTeam* that owns the *Data Science* environment, but on top of that he can access the
*Data Analysis* environment because her team has been invited by Maria.

!!! success "Pro tip!"
    You know whether you are `OWNER` or `INVITED` in an environment by checking **your Role** in that
    environment. This information appears in the picture in each environment box in the field "Role".

![](pictures/environments/env_teams_4.png#zoom#shadow)

!!! note "Difference between invited and owner"
    A team that has been invited to an environment has slight limitations, because well, it is not their environment!
    Invited teams cannot access the **Stack** tab of the environment because they should not be handling the resources
    of the environment. Same applies for **Tags** and **Subscriptions**. Other limitations come from the permissions that have
    been assigned to the team.

### :material-aws: **AWS access - Environment IAM roles**
For the environment admin team and for each team invited to the environment <span style="color:grey">*data.all*</span> 
creates an IAM role. From the **Teams** tab of
the environment we can assume our team's IAM role to get access to the AWS Console or copy the credentials to the
clipboard. Both options are under the "Actions" column in the Teams table (these options are only available if `core.features.env_aws_actions` is set to `True` in the `config.json` used for deployment of data.all).



![](pictures/environments/env_teams_3.png#zoom#shadow)


**Usage**

- Assumed by Team members from <span style="color:grey">*data.all*</span> UI to explore and work with data
- Credentials can be copied in <span style="color:grey">*data.all*</span> UI to explore and work with data
- Assumed by <span style="color:grey">*data.all*</span> Worksheets to query data using Athena

**IAM Permissions**

Default permissions

- read permissions to profiling/code folder in the Environment S3 Bucket
- Athena permissions to use the Team's workgroup
- CloudFormation permissions to resources tagged with Team tag and prefixed with environment `resource_prefix`
- SSM Parameter Store permissions to resources tagged with team tag and prefixed with environment `resource_prefix`
- Secrets Manager permissions to resources tagged with team tag and prefixed with environment `resource_prefix`
- read permissions on Logs and IAM
- PassRole permissions for itself to Glue, Lambda, SageMaker, StepFunctions and DataBrew

Data permissions

- read and write permissions to the Team-owned Dataset S3 Buckets
- encrypt/decrypt data with the Team-owned Dataset KMS keys
- read and write permissions Dataset Glue databases - governed with Lake Formation

Feature permissions

Depending on the features enabled in the environment and granted to the Team, additional AWS permissions
are given to the role. Permissions for any AWS service need to be defined to allow access onlt to resources tagged 
with team tag and prefixed with environment `resource_prefix`

!!! warning "Access denied? You need to tag resources when you create them"
    Since permissions to AWS services are restricted to team-tagged resources, you need to tag any new 
    resource that you create at creation time. 

Let's say you are using the "Engineers" IAM role in an environment that prefixes all resources with
the `resource_prefix` = "dataall" as in the following picture.

![](pictures/environments/env_teams_5.png#zoom#shadow)


Assuming the IAM role you will be able to create parameters prefixed by "dataall" and tagged
with a tag Team=Engineers, otherwise you will get AccessDenied errors.


![](pictures/environments/env_teams_6.png#zoom#shadow)

All the resources created in the environment stack are tagged with the tag `Team=EnvAdminTeam`, which means that 
environment admins can access and manage the environment baseline AWS resources.

**Data Governance with Lake Formation** 

We use AWS Lake Formation to govern Glue databases and tables. Using Lake Formation, we grant permissions to the 
Environment teams IAM roles to read and write the Glue databases and tables that the Team owns.
In other words, each environment team IAM role can only access the Glue databases and tables of the Datasets
that the team owns.



## :material-account-plus-outline: **Manage Consumption Roles**
<span style="color:grey">*data.all*</span> creates or imports one IAM role per Cognito/IdP group that we invite to the environment. With these IAM roles data producers and consumers
can ingest and consume data, but sometimes we want to consume data from an application that already has an execution role. To increase the flexibility in the data consumption patterns, data.all introduces Consumption Roles.

Any IAM role that exists in the Environment AWS Account can be added to <span style="color:grey">*data.all*</span>. In the **Teams** tab click on *Add Consumption Role*

![](pictures/environments/env_consumption_roles_1.png#zoom#shadow)

A window like the following will appear for you to introduce a name for the consumption role in data.all, the arn of the IAM role, the Team that owns the consumption role and whether data.all should manage the consumption role. Enabling "data.all managed" on the consumption role allows data.all to attach IAM policies to the role used for data.all related activities, such as sharing data, rather than having a user manually add those policies to the role.

Only members of this team and tenants of <span style="color:grey">*data.all*</span> can edit or remove the consumption role.

![](pictures/environments/env_consumption_roles_2.png#zoom#shadow)

![](pictures/environments/env_consumption_roles_3.png#zoom#shadow)

!!! success "Existing roles only"
    <span style="color:grey">*data.all*</span> checks whether that IAM role exists in the AWS account of the environment before adding it as a consumption role.

**Data Access**

- By default, a new consumption role does NOT have access to any data in <span style="color:grey">*data.all*</span>.
- The team that owns the consumption role needs to open a share request for the consumption role as discussed more in the Discover --> Shares section.

