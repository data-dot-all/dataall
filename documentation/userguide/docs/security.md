# **Security**
Details on data.all security-first approach to building a modern data workspace
## **Data and metadata on data.all**
### **Data virtualization**
data.all is a fully virtualized solution that does not involve moving data from existing storage layers.

Any queries run on the data.all are pushed to existing processing layers (e.g. directly to your database,
warehouse, or a processing layer such as Athena or Presto on top of S3).

### **Data and metadata storage**
Data and metadata collected and created by data.all are stored in applications and databases within the
customer’s VPC (virtual private cloud).
This includes information for data previews and queries, data quality, metadata, and user data.

### **Data previews and queries**
data.all gives users the ability to see sample data previews for a datasets and results for any queries run on data.all.

In both cases, the request is pushed upstream to the original data source, and a 100-row sample of the result is
provided to data.all users.

### **Data quality profile**
Users can generate data quality metrics with the click of a button on data.all. Once generated, these metrics are
stored in PostgreSQL on the customer’s VPC.

### **Metadata**
Dataset metadata, including metadata generated on data.all, is stored across Elasticsearch and Aurora PostgreSQL.

Elasticsearch is used to optimize search on the product, and Aurora PostgreSQL acts as a persistence backend.

### **User data**
Data on users, roles, and IdP groups is stored in a PostgreSQL database.

Any user data transmitted over the internet is SSL-encrypted over HTTPS.

### **Authentication**
The data.all authentication process is based SAML 2.0–based login. data.all can also integrate into organizations’
existing SAML 2.0–based SSO authentication systems.

### **AWS Web Application Firewall (WAF)**
Data.all supports the opportunity to add custom rules to AWS WAF. These rules are set in `cdk.json` at the root level of the repository.
As a custom rules (property `custom_waf_rules`) customer can set two allow lists:
* The Geo match allow-list (property `allowed_geo_list`) is an array of two-character country codes that you want to match against. 
If this property is specified, WAF will block web requests from all other countries, otherwise requests from all countries will be allowed.
* The IP match allow-list (property `allowed_ip_list`) is used to specify zero or more IP addresses or blocks of IP addresses. 
If this property is specified, WAF will block web requests from all other IP addresses, otherwise requests from all IP addresses will be allowed.

Example of custom WAF rules setting:
```json
{
  "app": "python ./deploy/app.py",
  "context": {
    "@aws-cdk/aws-apigateway:usagePlanKeyOrderInsensitiveId": false,
    "@aws-cdk/aws-cloudfront:defaultSecurityPolicyTLSv1.2_2021": false,
    "@aws-cdk/aws-rds:lowercaseDbIdentifier": false,
    "@aws-cdk/core:stackRelativeExports": false,
    "tooling_region": "eu-west-1",
    "custom_waf_rules": {
      "allowed_geo_list": [ "US", "CN" ],
      "allowed_ip_list":  ["192.0.2.44/32", "192.0.2.0/24", "192.0.0.0/16"] 
    },
    "DeploymentEnvironments": [
        {
            "envname": "dev",
            "account": "000000000000",
            "region": "eu-west-1",
            "enable_pivot_role_auto_create": true,
            "enable_opensearch_serverless": true
        }
    ]
  }
}
```

