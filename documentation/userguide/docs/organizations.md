# **Tenant and Organizations**

data.all manages teams' permissions at four levels:

1. Tenant team
2. Organization
3. Environment (next section)
4. Teams (next section)

## **Tenant**

data.all has a super user's team which is a group from your
IdP that has the right to manage high level application (tenant)
permissions for all IdP groups integrated with data.all.

This super user's team maps to a group from your IdP that's by default
named "***DAAdministrators***", any user member of this group will be
able to:

- create organizations
- manage tenant permissions on onboarded teams (IdP groups) as shown below.

### :material-account-plus-outline: **Manage tenant permissions**
As a user part of "***DAAdministrators***" on your IdP you can access
the settings menu from the profile icon.

For example, Maria Garcia is not part of "***DAAdministrators***", therefore she sees nothing

![](pictures/organizations/org_tenant_2.png#zoom#shadow)

On the other hand, Tenant user is part of this group and can navigate to **Admin settings**

![](pictures/organizations/org_tenant_1.png#zoom#shadow)

In *Admin Settings*, the Tenant user can manage tenant permissions. In the following picture, the user is NOT granting the
*DataScienceTeam* that John belongs to permissions to create an organization.

![](pictures/organizations/org_tenant_3.png#zoom#shadow)

If the tenant revokes the permission of a team to manage an object, that team won't be able to perform any action on
that particular object. For the given example, assuming that John only belongs to the *DataScienceTeam*,
he is not able to create organizations:

![](pictures/organizations/org_tenant_4.png#zoom#shadow)

## **Organizations**
Organizations are high level constructs where business units can collaborate across many different AWS accounts
at once. An organization includes environments and teams (see next section). Organizations are abstractions,
they **don't** contain AWS resources, consequently there is no CloudFormation stack associated with them.

*Organizations usually correspond to whole organizations, organization divisions or a separated geographical region
within an organization.*

### :material-new-box: **Create an organization**
!!! note "Organization permissions"
    Any user can create an organization as long as he or she belongs to a
    group with tenant permission "Manage Organizations" (see previous chapter, "Manage tenant permissions").

To create an organization, on the left pane select **Organization**, click **Create** and complete the following form.

![organization_form](pictures/organizations/org_tenant_5.png#zoom#shadow)


| Field             | Description | Required | Editable | Example
|-------------------|-------------|----------|----------|-------------
| Organization name |    Name of the organization         | Yes      | Yes      | AnyCompany EMEA
| Short description | Short description about the organization| No       | Yes      | AnyCompany EMEA region
| Team              | Name of the team managing the organization         | Yes      | No       | EMEAAdmin
| Tags              |  List of tags           | No       | Yes      |fin,rnd,mark,sales

The next step to onboard your IdP groups is to link an environment and add teams, check
<a href="environments.html">Link an environment</a> and <a href="environments.html">Add a team to an environment</a>

### :material-pencil-outline: **Edit and update an organization**
On the organisation window we can check the organization metadata, as well as the environments and teams that belong
to this organisation (we will come back to this in
<a href="environments.html">Environments and teams</a>).

To edit the metadata of the organisation, click in **Edit** and update the information. Name, description and tags are
editable, however the organisation team cannot be updated.

### :material-trash-can-outline: **Delete an organization**
!!! danger "Warning"
    Make sure that you delete the organisation environments before deleting the organisation. Otherwise, orphan
    environments might run into conflicts.

To archive an organisation, click on the **Archive** button next to the Edit button. A window with the previous
warning will appear. If you want to go ahead and delete the organization, type *permantly archive* in the box and
submit.
