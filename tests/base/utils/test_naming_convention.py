from dataall.base.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)


def test_s3_bucket_name():
    service = NamingConventionService(
        target_uri='yTrfS',
        target_label='my-bucket/name-*_ert19my-bucket/name-*_ert19my-bucket/name-*_ert19my-bucket/name-*_ert19',
        pattern=NamingConventionPattern.S3,
        resource_prefix='customerverylongprefix',
    )
    compliant_bucket_name = service.build_compliant_name()
    assert '/' not in compliant_bucket_name
    assert '_' not in compliant_bucket_name
    assert '*' not in compliant_bucket_name


def test_iam_role_name():
    service = NamingConventionService(
        target_uri='yTrfS',
        target_label='MyA_mzin*Er-oleMyA_mzin*Er-oleMyA_mzin*Er-oleMyA_mzin*Er-ole',
        pattern=NamingConventionPattern.IAM,
        resource_prefix='customerverylongprefix',
    )
    compliant_iam_role_name = service.build_compliant_name()
    assert '_' in compliant_iam_role_name
    assert '*' not in compliant_iam_role_name


def test_glue_database_name_():
    service = NamingConventionService(
        target_uri='yTrfS',
        target_label='my-long-db' * 40,
        pattern=NamingConventionPattern.GLUE,
        resource_prefix='customerverylongprefix',
    )
    compliant_db_name = service.build_compliant_name()
    assert '-' not in compliant_db_name


def test_default_name():
    service = NamingConventionService(
        target_uri='yTrfS',
        target_label='MyA_mzin*Er-ole',
        pattern=NamingConventionPattern.DEFAULT,
        resource_prefix='customerverylongprefix',
    )
    compliant_default_name = service.build_compliant_name()
    assert '_' in compliant_default_name
    assert '*' not in compliant_default_name
