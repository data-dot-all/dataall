# **Notebooks**

Data practitioners can experiment machine learning algorithms
spinning up Jupyter notebook with access to all your datasets. data.all leverages
<a href="https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html" target="_blank">
Amazon SageMaker instance</a> to access Jupyter notebooks.


## :material-new-box: **Create a Notebook**
!!! warning "Pre-requisites"
    To use Notebooks you need to introduce your own VPC ID or create a Sagemaker Studio domain inside a VPC
    (read the <a href="https://docs.aws.amazon.com/sagemaker/latest/dg/onboard-vpc.html" target="_blank">docs</a>).
    Provisioning the notebook instances inside a VPC enables the notebook to access VPC-only
    resources such as EFS file systems.


To create a Notebook, go to Notebooks on the left pane and click on the **Create** button. Then fill in the following form:

![notebooks](pictures/notebooks/nb_form.png#zoom#shadow)

| Field                      | Description                                    | Required | Editable |Example
|----------------------------|------------------------------------------------|----------|----------|-------------
| Sagemaker instance name    | Name of the notebook                           | Yes      | No       |Cannes Project
| Short description          | Short description about the notebook           | No       | No       |Notebook for Cannes exploration
| Tags                       | Tags                                           | No       | No       |deleteme
| Environment                | Environment (and mapped AWS account)           | Yes      | No       |Data Science
| Region (auto-filled)       | AWS region                                     | Yes      | No       |Europe (Ireland)
| Organization (auto-filled) | Organization of the environment                | Yes      | No       | AnyCompany EMEA
| Team                       | Team that owns the notebook                    | Yes      | No       |DataScienceTeam
| VPC Identifier    | VPC provided to host the notebook              | No       | No       | vpc-......
| Public subnets    | Public subnets provided to host the notebook   | No       | No       | subnet-....
| Instance type              | [ml.t3.medium,  ml.t3.large,     ml.m5.xlarge] | Yes      | No       |ml.t3.medium
| Volume size                | [32, 64, 128, 256]                             | Yes      | No       |32


If successfully created we can check its metadata in the **Overview** tab. Unlike other data.all resources, Notebooks
are non-editable.

![notebooks](pictures/notebooks/nb_overview.png#zoom#shadow)

## :material-cloud-check-outline: **Check CloudFormation stack**
In the **Stack** tab of the Notebook, is where we check the AWS resources provisioned by data.all as well as its status.
As part of the Notebook CloudFormation stack deployed using CDK, data.all will deploy:

1. AWS EC2 Security Group
2. AWS SageMaker Notebook Instance
3. AWS KMS Key and Alias


## :material-trash-can-outline: **Delete a Notebook**

To delete a Notebook, simply select it and click on the **Delete** button in the top right corner. It is possible to
keep the CloudFormation stack associated with the Notebook by selecting this option in the confirmation
delete window that appears after clicking on delete.

![buttons](pictures/notebooks/nb_buttons.png#zoom#shadow)

## :material-file-code-outline: **Open JupyterLab**
Click on the **Open JupyterLab** button of the Notebook window to start writing code on Jupyter Notebooks.

![buttons](pictures/notebooks/nb_jupyter.png#zoom#shadow)

## :material-stop-circle-outline: **Stop/Start instance**
As we briefly commented, data.all uses AWS SageMaker instances to access Jupyter notebooks. Be frugal and stop your
instances when you are not developing. To do that, close the Jupyter window and click on
**Stop Instance** in the Notebook buttons. It takes a couple of minutes, just refresh and check the Notebook Status
in the overview tab. It should end up in `STOPPED`.

!!! success "Save money, stop your instances"
    This feature allows users to easily manage their instances directly from data.all UI.

Same when you are coming back to work on your Notebook, click on **Start instance** to start the SageMaker instance.
In this case the Status of the notebook should first be `PENDING` and once the instance is ready, `INSERVICE`.

## :material-tag-remove-outline: **Create Key-value tags**

In the **Tags** tab of the notebook window, we can create key-value tags. These tags are not <span style="color:grey">*data.all*</span> tags
that are used to tag datasets and find them in the catalog. In this case we are creating AWS tags as part of the
notebook CloudFormation stack. There are multiple tagging strategies as explained in the
<a href="https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html">documentation</a>.
