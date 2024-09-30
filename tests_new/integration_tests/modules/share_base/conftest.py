import pytest


@pytest.fixture(params=['Group', 'ConsumptionRole'])
def principal1(request, group5, consumption_role_1):
    if request.param == 'Group':
        yield group5, request.param
    else:
        yield consumption_role_1.consumptionRoleUri, request.param


@pytest.fixture(params=['Group', 'ConsumptionRole'])
def share_params_main(request, session_share_1, session_share_consrole_1, session_s3_dataset1):
    if request.param == 'Group':
        yield session_share_1, session_s3_dataset1
    else:
        yield session_share_consrole_1, session_s3_dataset1


@pytest.fixture(params=[(False, 'Group'), (True, 'Group'), (False, 'ConsumptionRole'), (True, 'ConsumptionRole')])
def share_params_all(
    request,
    session_share_1,
    session_share_consrole_1,
    session_s3_dataset1,
    session_share_2,
    session_share_consrole_2,
    session_imported_sse_s3_dataset1,
):
    autoapproval, principal_type = request.param
    if autoapproval:
        if principal_type == 'Group':
            yield session_share_2, session_imported_sse_s3_dataset1
        else:
            yield session_share_consrole_2, session_imported_sse_s3_dataset1
    else:
        if principal_type == 'Group':
            yield session_share_1, session_s3_dataset1
        else:
            yield session_share_consrole_1, session_s3_dataset1
