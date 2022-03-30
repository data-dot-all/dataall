# **FAQs**


## **1. General**
### **What is a data workspace**
A Data Workspace is an analytical environment, that is meant to store data from various teams and even organizations together to make data highly available, easily discoverable and secure.

### **What is Data.all**
A modern data workspace that makes collaboration among diverse users (like business, analysts and engineers) easier, increasing efficiency and agility in data projects.

### **Can I use Data.all oustside of AWS**
Data.all has been built on top of Native AWS Service (AWS Lake Formation, Amazon S3...), thus Data.all exclusively works within an AWS ecosystem.
if you plan to use it in hybrid (on-prem/other cloud providers) you will have to create your own integration with Data.all engine. 

## **2. Troubleshooting**
### **CI/CD deployment**
**Error: Can't add a gateway endpoint to VPC; route table IDs are not available**: Usually this error is related to AWS CDK not able to find the route tables of the VPC that you would like to reuse in CDK context (cdk.json); you should create route tables for your VPC if you VPC do not have one.
  
### **I have red errors on the frontend**
**CORS error**:<br>
In case of healthy deployment (pipeline successfully finished), the CORS issue is related to cold start of RDS Aurora, in case of a production environment, you can choose to set the **prod_sizing** in your cdk.json to **true** to pause the Aurora after 24 hours rather than 10 minutes.
  
The most straightforward way to know the reason of the red error in the frontend, is to inspect the console in your browser, and to start the troubleshooting from the Authorization lambda (Please refer to Data.all architecture for the flow)