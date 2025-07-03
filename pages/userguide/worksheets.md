---
layout: default
sublevel: true
back_link: /dataall/userguide/
title: Worksheets
permalink: /userguide/worksheets/
---
# **Worksheets**

data.all offers a rich editor to write SQL queries and explore data. It is Athena on the backend that runs our queries
on environments where our teams have been onboarded.


## 📦 **Create a Worksheet**
On the left pane under **Play** click on **Worksheets** to go to the Worksheet menu. Here you will find all
Worksheets owned by your teams.

> **✅ Shared queries = Seamless Collaboration**
>
> Check, learn from and collaborate with other members of your team to improve your analyses and get insights from
> your data, directly from data.all worksheets. No need to send queries by email, no need to create views :)


To create a new worksheet click on the **Create** button in the top right corner and fill the Worksheet form:

![worksheets](img/worksheets/ws_form.png#zoom#shadow)

| Field             | Description                                | Required | Editable |Example
|-------------------|--------------------------------------------|----------|----------|-------------
| Worksheet name    | Name of the worksheet                      | Yes      | Yes      |PalmDor
| Short description | Short description about the worksheet      | No       | Yes      |Query used to retrieve Palm D'or winners
| Team              | Team that owns the worksheet               | Yes      | No       |DataScienceTeam
| Tags              | Tags  | No       | Yes      |adhoc

> **📝 No AWS resources**
>
> When we are creating a worksheet we are NOT deploying AWS resources. We don't provision clusters, we are not creating
> tables or views. We simply store the query in data.all database and we run it serverlessly on AWS Athena.


## ✏️ **Edit worksheet metadata**
Select a worksheet and click on the pencil icon to edit the metadata of the worksheet. This includes worksheet name,
description and tags. The ownership of the worksheet, its team, is not editable.

## 🗑️ **Delete a worksheet**
Next to the edit button, there are 2 other buttons. To delete a worksheet click on the trash icon one. Worksheets
are not AWS resources, they are a data.all construct whose information is stored in the data.all database. Thus,
when we delete a worksheet we are not deleting AWS resources or CloudFormation stacks.

## 🔍 **Write and save your queries**
Select your worksheet and choose any of the environments, datasets and tables of your team to list column information.
In the query editor write your SQL statements and click on **Run Query** to get your query results. Error messages
coming from Athena will pop-up automatically.

![worksheets](img/worksheets/ws_joins.png#zoom#shadow)

If you want to save the current query for later or for other users, click on the **save** icon (between the edit and the
delete buttons).

> **✅ More than just SELECT**
>
> Worksheets can be used for data exploration, for quick ad-hoc queries and for more complicated queries that require
> joins. As far as you have access to the joined datasets you can combine information from multiple tables or datasets.
> Check the <a href="https://docs.aws.amazon.com/athena/latest/ug/select.html" target="_blank">docs</a>
> for more information on AWS Athena SQL syntax.



