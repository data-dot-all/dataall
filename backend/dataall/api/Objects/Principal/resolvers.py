from .... import db


def get_principal(session, principalId, principalType=None, environmentUri=None):
    if principalType in ['Group', 'ConsumptionRole']:
        environment = db.api.Environment.get_environment_by_uri(session, environmentUri)
        organization = db.api.Organization.get_organization_by_uri(
            session, environment.organizationUri
        )
        return {
            'principalId': principalId,
            'principalType': principalType,
            'principalName': f'{principalId} ({environment.name}/{environment.region})',
            'AwsAccountId': environment.AwsAccountId,
            'SamlGroupName': principalId,
            'region': environment.region,
            'organizationUri': organization.organizationUri,
            'organizationName': organization.name,
        }
