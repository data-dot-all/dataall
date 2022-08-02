# **ML Studio**
With ML Studio Notebooks we can add users to our SageMaker domain and open Amazon SageMaker Studio


## :material-new-box: **Create a ML Notebook**
To create a new Notebook, go to ML Studio on the left side pane and click on Create. Then fill in the creation form
with its corresponding information.

![notebooks](pictures/mlstudio/ml_studio.png#zoom#shadow)


| Field                         | Description                                 | Required | Editable |Example
|-------------------------------|---------------------------------------------|----------|----------|-------------
| Sagemaker Studio profile name | Name of the user to add to SageMaker domain | Yes      | No       |johndoe
| Short description             | Short description about the notebook        | No       | No       |Notebook for Cannes exploration
| Tags                          | Tags                                        | No       | No       |deleteme
| Environment                   | Environment (and mapped AWS account)        | Yes      | No       |Data Science
| Region (auto-filled)          | AWS region                                  | Yes      | No       |Europe (Ireland)
| Organization (auto-filled)    | Organization of the environment             | Yes      | No       |AnyCompany EMEA
| Team                          | Team that owns the notebook                 | Yes      | No       |DataScienceTeam



## :material-cloud-check-outline: **Check CloudFormation stack**
In the **Stack** tab of the ML Studio Notebook, is where we check the AWS resources provisioned by data.all as well as its status.
As part of the CloudFormation stack deployed using CDK, data.all will deploy some CDK metadata and a SageMaker User Profile.


## :material-trash-can-outline: **Delete a Notebook**

To delete a Notebook, simply select it and click on the **Delete** button in the top right corner. It is possible to
keep the CloudFormation stack associated with the Notebook by selecting this option in the confirmation
delete window that appears after clicking on delete.

![notebooks](pictures/mlstudio/ml_studio_3.png#zoom#shadow)

## :material-file-code-outline: **Open Amazon SageMaker Studio**
Click on the **Open ML Studio** button of the ML Studio notebook window to open Amazon SageMaker Studio.

![notebooks](pictures/mlstudio/ml_studio_2.png#zoom#shadow)
