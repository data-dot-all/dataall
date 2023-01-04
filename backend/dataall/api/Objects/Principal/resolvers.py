from .... import db


def get_principal(session, principalId, principalType=None, principalIAMRoleName=None, environmentUri=None, groupUri=None):
    if principalType in ['Group', 'ConsumptionRole']:
        environment = db.api.Environment.get_environment_by_uri(session, environmentUri)
        organization = db.api.Organization.get_organization_by_uri(
            session, environment.organizationUri
        )
        if principalType in ['ConsumptionRole']:
            principal = db.api.Environment.get_environment_consumption_role(session, principalId, environmentUri)
            principalName = f"{principal.consumptionRoleName} [{principal.IAMRoleArn}]"
        else:
            principal = db.api.Environment.get_environment_group(session, groupUri, environmentUri)
            principalName = f"{groupUri} [{principal.environmentIAMRoleArn}]"

        return {
            'principalId': principalId,
            'principalType': principalType,
            'principalName': principalName,
            'principalIAMRoleName': principalIAMRoleName,
            'SamlGroupName': groupUri,
            'environmentUri': environment.environmentUri,
            'environmentName': environment.label,
            'AwsAccountId': environment.AwsAccountId,
            'region': environment.region,
            'organizationUri': organization.organizationUri,
            'organizationName': organization.label,
        }
