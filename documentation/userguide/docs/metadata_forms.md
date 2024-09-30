# **Metadata Forms**

**Concepts**

Metadata forms allow users to add structured contextual information to various entities in the Data.all platform. By creating and attaching metadata forms, user can standardize and enrich metadata in a customizable way.

Metadata forms serve several key purposes:

- Improve data discovery by enabling more consistent, complete, and meaningful metadata
- Capture domain-specific or organizational metadata standards
- Enforce governance policies around data documentation
- Facilitate data lineage and impact analysis
- Streamline metadata management workflows

![metadata form levels](pictures/metadata_forms/mf_levels.jpg#zoom#shadow)

This user guide provides instructions on how to create, manage, and use metadata forms in data.all. It covers form creation, attaching forms to entities, filling out forms, managing form visibility and permissions, and enforcing form usage. Whether you are a data producer adding metadata, a data consumer leveraging it, or an administrator standardizing on formats, this guide will help you get the most value out of metadata forms.

With customizable forms that can be attached across many entities, metadata forms provide a flexible and extensible mechanism for metadata management. Use this guide to learn how to configure and apply forms to address your specific metadata use cases and data governance needs.

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
When the editor mode is enabled, user can 

1. add fields using the button '+ Add field' in the left upper corner of the table;
2. delete fields using 'bin' icon in the end of the table row. When the user pushes the button, the row is disabled, which indicates it is marked for deletion, but user can restore the field by clicking the button (now with "refresh") again;
3. arrange fields using drag and drop;
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

In the column on the left all attached metadata forms are listed. When user clicks on the form, it content appears
on the right. The attached form can be deleted by click on "bin" icon next to form name in the list.

![metadata form attached_list](pictures/metadata_forms/attached_mf_list.png#zoom#shadow)

If user has permission to attach metadata forms to this entity, the button "+ Attach Form" appears over the attached metadata form list.
After user clicks this button and selects the available form from drop-dow list, they can fill in the form displayed on the right.
After all required fields are filled, press "Attach" button in the right upper corner of the editing area.

![metadata form attach](pictures/metadata_forms/attach_mf.png#zoom#shadow)
