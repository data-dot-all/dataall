# **Metadata Forms**

**Introduction**

Metadata forms allow data.all users to add structured contextual information to various entities in the data.all platform. By creating and attaching metadata forms, users can standardize and enrich metadata in a customizable way.

Metadata forms serve several key purposes:

- Improve data discovery by enabling more consistent, complete, and meaningful metadata
- Capture domain-specific or organizational metadata standards
- Streamline metadata management workflows
- Search among all entities in data.all based on attached metadata

**Metadata Forms visibility**

Visibility setting defines who can view and attach a metadata form to an entity.

- Global visibility means the metadata form is visible and attachable to any entity by all users across the platform
- Organization/Environment-Wide visibility limits the form to a specific organization/environment - it can only be seen by members of this organization/environment and attached to entities in that organization/environment
- Team-Only visibility restricts the form to just members of a specific team, but does not restrict to which entities it can be attached to

The same visibility restrictions apply to the attached metadata form. For example, if userA can see Metadata Form A, but can't see Metadata Form B, and both of these metadata forms are attached to a dataset; then when userA opens the dataset, they will see the attached metadata form A but not the attached metadata form B.

**Metadata Form lifecycle and usage**

1. User given the permission from data.all administrators can create metadata forms with the Global visibility and visibility for their teams. Owners and Admins of Organizations and Environments can create metadata forms with Environment-Wide and Organization-wide visibility for owned entities.
2. Once form is created, the owners can add enforcement rules (see the section below).
3. All changes in metadata form can be performed only by its owner. 
4. In case owner deletes metadata form all its attached entities are deleted in cascade mode. 
5. Metadata form can be attached to an entity by the user with sufficient permissions. Permissions are given by the owner or admin of the entity (in case of Environments and Organizations). In case of Datasets the owner and steward teams have these permissions and also the teams with whom the dataset was shared.
6. Attached metadata forms can be edited or deleted by any user with sufficient permissions.

**Metadata Forms levels and enforcement**

Metadata forms can be obligatory to fill in on different levels. User can select the metadata form and entity types, that should have this form attached.  Enforcement affects selected entity types on all lower levels hierarchically.

![metadata form levels](pictures/metadata_forms/mf_levels.jpg#zoom#shadow)

Who can enforce:

* Data.all admins can enforce any form on any level across the platform. They have full control over metadata form enforcement.
* Owners/admins  of a data.all entity can enforce forms for this levels and levels below in the hierarchy. For example, an org admin can enforce a form for the org, all teams in that org, all environments in the org, all datasets in those environments, etc.
* Share approvers and requestors can enforce forms for a specific share they are involved with. However, they can only delete enforcement rules they created themselves - they cannot delete rules created by others

So in summary, enforcement capabilities cascade along with administrative privileges in the hierarchy. Global admins have full control, org/env admins can enforce for their sphere and below, dataset admins for the datasets and items in it, and share requesters and approvers for a specific share.

**View Metadata Forms**
By clicking Metadata Forms in the Discovery section of the left side pane users can open a list of metadata forms visible for them.
The criteria for visibility:
1. The group, that the user belong to, is an owner of the metadata form.
2. Metadata form has Global visibility.
2. Metadata form has Team-Only visibility and the user is a member of this team.
3. Metadata form has Environment-Wide of Organization-Wide visibility and the user has access to this environment/organization.
4. Administrators can view all metadata forms.

![metadata form list](pictures/metadata_forms/mf_list.png#zoom#shadow)

**Create Metadata Form**

To create a new metadata form:

1. Navigate to the Metadata Forms page under the Discovery section.

2. Click the "New Metadata Form" button in the top right corner.

3. In the pop-up dialog, enter a Name and Description for the form.

4. Select the Owner Team responsible for managing this form.

5. Choose a Visibility level to control access to the form. Options are Team Only, Environment-Wide, Organization-Wide, or Global.

6. If Visibility is not Global, select the Organization, Environment ot Team to scope the form.

7. Click "Create" to generate the form.

![metadata form create](pictures/metadata_forms/mf_create.png#zoom#shadow)

You will be redirected to the metadata form page. It contains details overview, instruments to edit form fields and preview tab.

In the field editor, use the "Edit" button in the upper right corner of the table to update fields. 
When the editor mode is enabled, the user can 

1. add fields using the button '+ Add field' in the left upper corner of the table;
2. delete fields using 'bin' icon in the end of the table row. When the user pushes the button, the row is disabled, which indicates it is marked for deletion, but user can restore the field by clicking the button (now with "refresh") again;
3. arrange fields using drag and drop, fields will be shown in rendered metadata form in the order they appear in this list (from top to bottom);
4. edit all parameters of the field.

When finished, click "Save" to apply changes.

![metadata form fields](pictures/metadata_forms/mf_edit_fields.png#zoom#shadow)

In the "Preview" tab user can see, how the form will be rendered.

![metadata form preview](pictures/metadata_forms/mf_preview.png#zoom#shadow)

The new metadata form can now be attached to entities and filled out by users with access. 
Forms can be edited later to modify fields and settings.

User can delete the form with button "Delete" in the upper right corner of the form view page.

**Attach Metadata Form**

User with required access can attach metadata form to Organization, Environment or Dataset.
To attach new metadata form or view already attached use the tab "Metadata" on entity view page.

In the column on the left all attached metadata forms are listed. When the user clicks on the form, its content appears
on the right. The attached form can be deleted by click on "bin" icon next to form name in the list.

![metadata form attached_list](pictures/metadata_forms/attached_mf_list.png#zoom#shadow)

If user has permission to attach metadata forms to this entity, the button "+ Attach Form" appears over the attached metadata form list.
After user clicks this button and selects the available form from drop-dow list, they can fill in the form displayed on the right.
After all required fields are filled, press "Attach" button in the right upper corner of the editing area.

![metadata form attach](pictures/metadata_forms/attach_mf.png#zoom#shadow)


**Permissions Summary**
1. **Create Metadata Form:** User given the permission from data.all administrators can create metadata forms with the Global visibility and visibility for their teams. Owners and Admins of Organizations and Environments can create metadata forms with Environment-Wide and Organization-wide visibility for owned entities.
2. **Edit and delete Metadata Form:** These actions available only for owners of the metadata form.
3. **Enforce Metadata Form Usage**: 

* Data.all admins can enforce any form on any level across the platform. They have full control over metadata form enforcement.
* Owners/admins  of a data.all entity can enforce forms for these levels and levels below in the hierarchy. For example, an org admin can enforce a form for the org, all teams in that org, all environments in the org, all datasets in those environments, etc.
* Share approvers and requestors can enforce forms for a specific share they are involved with. However, they can only delete enforcement rules they created themselves - they cannot delete rules created by others

4. **Attach Metadata Form**: 

* Users must have relevant  permissions for target entity (ATTACH_METADATA_FORM, given by entity admin)
* Users must have access to view the target metadata form (see paragraph "View Metadata Forms")
* Target entity must be in target metadata form scope (see paragraph "Metadata Forms Levels")

5. **Delete Attached Metadata Form**:  Users must have relevant  permissions for target entity (ATTACH_METADATA_FORM, given by entity admin)