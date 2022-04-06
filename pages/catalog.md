# **Centralized Catalog and glossaries**

## **Catalog**

In the Catalog we have a record with metadata for each dataset, table, folder and dashboard in data.all. Users come to
this centralized Catalog to search and find data owned by other teams. Once users find a data asset they are
interested in, they will create a <a href="shares.html">Share</a> request.

**How do users find the data that they need?**

Data needs to be discoverable, for this reason data.all Catalog offers a variety of filters that use
business context to improve your search:

- **Type of data**: `dataset`,`table`, `folder` and/or `dashboard`
- **Tags**: tags of the data asset.
- **Topics**: filter by general topics created by the user.
- **Region**: AWS region where the data asset is located.
- **Classification**: `unclassified`, `official` and/or `secret`
- **Glossary**: filter datasets by the glossary terms created by users. This helps in two ways:
It lets you narrow down results quickly using granular glossary terms like "sales", "profit", etc.
Traditionally, a data glossary is just used to organize data. However, data.all uses it to power its search.
This further encourages users to enrich and maintain the glossary regularly.

![](pictures/catalog/catalog_1.png#zoom#shadow)

## **Glossaries**

A Glossary is a list of terms, organized in a way to help users understand the context of their datasets.
For example, terms like "cost", "revenue", etc, can be used to group and search all financial datasets.

The use of familiar terminology helps in quickly understanding the data and its background.
It is a crucial element of data governance as it helps in bringing the business understanding closer to
an organization's data initiatives.

On data.all, glossary terms can be attached to any dataset and can be leveraged to power quick and ease data discovery in
the Catalog.

!!!success "**Spotlight**"
    Glossaries are built hierarchically. They are made of categories and terms.
    This structure allows for glossaries from multiple domains to co-exist.


**Term:**

- A term is the lowest unit which is unique inside each glossary.
- It describes the content of the data assets in the most useful and precise way.
- It can exist independently, without belonging to any particular category or sub-category.


**Category:**

A category is used to group the terms of a similar context together. it is just a way of organizing terms.


### **Create a new glossary**

1. Go to **Glossaries** menu on the elft side pane.
2. Click on **Create**.
3. Fill the form and add a new glossary.

![create_glossary](pictures/catalog/glos_1.png#zoom#shadow)


### **Add a category inside a Glossary**

1. Click on the button "Add category" to add a new category.
2. Add a name and description to your category for better understanding.

![add_category](pictures/catalog/glos_2.png#zoom#shadow)

### **Add terms to a category**

1. Click on the button "Add term" to add a new term to the category.
2. Give it an appropriate name and description.

![add_term](pictures/catalog/glos_3.png#zoom#shadow)


!!! abstract "Remember!"
    The term will be used to recognize and filter the datasets. Hence, keep it short and precise.

### **Link your data with appropriate glossary terms**
You can associate a glossary term to a dataset or a table. Go to a dataset click on "edit" and update
the glossary terms field as shown below:

![link_term](pictures/catalog/glos_4.png#zoom#shadow)

### **Check all data related to a glossary**
To see a list of all datasets and tables that have been linked with terms of a specific glossary, go to Glossaries
and select the glossary. In the **Associations** tab it is possible to check the related data assets (target name),
their types (e.g. dataset) and the specific term that they have used.

![relatedterm](pictures/catalog/glos_5.png#zoom#shadow)
