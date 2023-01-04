# **Environments and Teams**

An environment is a **workplace** where a team can bring, process, analyze data and build data driven applications.
Environments comprise AWS resources, thus when we create an environment, we deploy a CDK/CloudFormation stack
to an AWS account and region. In other words, **an environment is mapped to an AWS account in one region, where
users store data and work with data.**

!!! danger "One AWS account, One environment"
    To ensure correct data access and AWS resources isolation, onboard one environment in each AWS account.
    Despite being possible, **we strongly discourage users to use the same AWS account for multiple environments**.

## :material-hammer-screwdriver: **Bootstrap your AWS account**
*data.all*does not create AWS accounts. You need to provide an AWS account and complete the following bootstraping
steps on that AWS account in each region you want to use.

### 1. Create AWS IAM role
<span style="color:grey">*data.all*</span> assumes a IAM role named **PivotRole** to be able to call AWS SDK APIs on your account. You can download
the AWS CloudFormation stack from <span style="color:grey">*data.all*</span> environment creation form. (Navigate to an
organization and click on link an environment to see this form)


### 2. Setup AWS CDK

<span style="color:grey">*data.all*</span> uses AWS CDK to deploy and manage resources on your AWS account.
AWS CDK requires some resources to exist on the AWS account, and provides a command called `bootstrap` to deploy these
specific resources.

Moreover, we need to trust data.all infrastructure account.
data.all codebase and CI/CD resources are in the data.all **tooling account**,
while all the resources used by the platform
are located in a **infrastructure account**. From this last one we will deploy environments and other resources
inside each of our business accounts (the ones to be boostraped).


To boostrap the AWS account using AWS CDK, you need :

1. to have AWS credentials configured in ~/.aws/credentials or as environment variables.
2. to install cdk : `npm install -g aws-cdk`
3. to run the following command :
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



### 3. Enable AWS Lake Formation
<span style="color:grey">*data.all*</span> relies on AWS Lake Formation to manage access to your structured data.
If AWS Lake Formation has never been
activated on your AWS account, you need to create
a service-linked role, using the following command:

```bash
aws iam create-service-linked-role --aws-service-name lakeformation.amazonaws.com
```

!!! danger "Service link creation error"
    If you receive: An error occurred (InvalidInput) when calling the CreateServiceLinkedRole operation: Service
    role name AWSServiceRoleForLakeFormationDataAccess has been taken in this account, please try a different suffix.
    <b>You can skip this step, as this indicates the Lake formation service-linked role exists.</b>

### 4. Amazon Quicksight

This is an optional step. To link environments with <i><b>Dashboards enabled</b></i> , you will also need a running Amazon QuickSight subscription
on the bootstraped account. If you have not subscribed to Quicksight before, go to your AWS account and choose the
Enterprise option as show below:

![quicksight](pictures/environments/boot_qs_1.png#zoom#shadow)

![quicksight](pictures/environments/boot_qs_2.png#zoom#shadow)

After you've successfully subscribed to QuickSight, we need to trust <span style="color:grey">*data.all*</span> domain on QuickSight
to enable Dashboard Embedding on <span style="color:grey">*data.all*</span> UI. To do that go to:

1. Manage QuickSight
2. Domains and Embedding
3. Put <span style="color:grey">*data.all*</span> domain and check include subdomains
4. Save

![quicksight_domain](pictures/environments/boot_qs_3.png#zoom#shadow)

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
| IAM Role name     | Alternative name of the environment IAM role                                                                                              | No       | No       |anotherRoleName
| Resources prefix  | Prefix for all AWS resources created in this environment. Only (^[a-z-]*$)                                                                | Yes      | Yes      |fin
| Team              | Name of the group initially assigned to this environment                                                                                  | Yes      | No       |FinancesAdmin
| Tags              | Tags that can later be used in the Catalog                                                                                                | Yes      | Yes      |finance, test
| VPC Identifier    | VPC provided to host the environment resources instead than the default one created by <span style="color:grey">*data.all*</span>         | No       |   No       | vpc-......
| Public subnets    | Public subnets provided to host the environment resources instead than the default created by <span style="color:grey">*data.all*</span>  | No       |  No        | subnet-....
| Private subnets   | Private subnets provided to host the environment resources instead than the default created by <span style="color:grey">*data.all*</span> | No       |   No       | subnet-.....


**Features Management**

An environment is defined as a workspace and in this workspace we can flexibly activate or deactivate different
features, adapting the workspace to the teams' needs. If you want to use Dashboards, you need to complete the optional
fourth step explained in the previous chapter "Bootstrap your AWS account".

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
- Networks: VPCs created and owned by the environment
- Warehouses: Redshift clusters imported or created in this environment
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

Note that we can keep the environment CloudFormation stack. What is this for? This is useful in case you want to keep
using the environment resources (IAM roles, etc) created by <span style="color:grey">*data.all*</span> but outside of <span style="color:grey">*data.all*</span>

### :material-plus-network-outline: **Create networks**
Networks are VPCs created from <span style="color:grey">*data.all*</span> and belonging to an environment and team. To create a network, click in the
**Networks** tab in the environment window, then click on **Add** and finally fill the following form.

!!!abstract "I need an example!"
    What is the advantage of using networks from <span style="color:grey">*data.all*</span>? ....[MISSING INFO]


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
new IAM role for the new team. The IAM role policies mapped to the permissions granted to the invited team
(e.g., a team  invited without "Create Redshift clusters" permission will not have
redshift permissions on the associated IAM role).To remove a group, in the *Actions* column select the minus icon.


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

### :material-aws: **AWS access**
<span style="color:grey">*data.all*</span> makes it easier to manage access to your AWS accounts. How? remember when we assigned granular AWS permissions
to invited groups and this created an IAM role? (If not, check the "Manage teams" section). From the **Teams** tab of
the environment we can assume our team's IAM role to get access to the AWS Console or copy the credentials to the
clipboard. Both options are under the "Actions" column in the Teams table.

## :material-account-plus-outline: **Manage Consumption Roles**
Data.all creates or imports one IAM role per Cognito/IdP group that we invite to the environment. With these IAM roles data producers and consumers
can ingest and consume data, but sometimes we want to consume data from an application such as SageMaker pipelines,
Glue Jobs or any other downstream application. To increase the flexibility in the data consumption patterns, data.all introduces Consumption Roles.

Any IAM role that exists in the Environment AWS Account can be added to data.all. In the **Teams** tab click on *Add Consumption Role*

![](pictures/environments/env_consumption_roles_1.png#zoom#shadow)

A window like the following will appear for you to introduce the arn of the IAM role and the Team that owns the consumption role.
Only members of this team and tenants of data.all can remove the consumption role.

![](pictures/environments/env_consumption_roles_2.png#zoom#shadow)

!!! success "Existing roles only"
    Data.all checks whether that IAM role exists in the AWS account of the environment before adding it as a consumption role.

**Data Access**

- By default, a new consumption role does NOT have access to any data in data.all.
- The team that owns the consumption role needs to open a share request for the consumption role as shown in the picture below.

