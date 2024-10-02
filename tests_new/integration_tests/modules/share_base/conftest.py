import pytest


@pytest.fixture(params=['Group', 'ConsumptionRole'])
def principal1(request, group5, session_consumption_role_1):
    if request.param == 'Group':
        yield group5, request.param
    else:
        yield session_consumption_role_1.consumptionRoleUri, request.param


# --------------SESSION PARAM FIXTURES----------------------------


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


# --------------PERSISTENT FIXTURES----------------------------


@pytest.fixture(params=['Group', 'ConsumptionRole'])
def persistent_share_params_main(request, persistent_role_share_1, persistent_group_share_1):
    if request.param == 'Group':
        yield persistent_group_share_1
    else:
        yield persistent_role_share_1
