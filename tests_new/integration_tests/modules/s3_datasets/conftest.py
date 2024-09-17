TABLES_FIXTURES_PARAMS = (
    'tables_fixture_name',
    [
        'session_s3_dataset1_tables',
        'session_imported_sse_s3_dataset1_tables',
        'session_imported_kms_s3_dataset1_tables',
    ],
)

DATASETS_FIXTURES_PARAMS = (
    'dataset_fixture_name',
    [
        'session_s3_dataset1',
        'session_imported_sse_s3_dataset1',
        'session_imported_kms_s3_dataset1',
    ],
)

DATASETS_TABLES_FIXTURES_PARAMS = (
    'dataset_fixture_name,tables_fixture_name',
    [
        ('session_s3_dataset1', 'session_s3_dataset1_tables'),
        ('session_imported_sse_s3_dataset1', 'session_imported_sse_s3_dataset1_tables'),
        ('session_imported_kms_s3_dataset1', 'session_imported_kms_s3_dataset1_tables'),
    ],
)

TABLES_CONFIDENTIALITY_FIXTURES_PARAMS = (
    'tables_fixture_name, confidentiality',
    [
        ('session_s3_dataset1_tables', 'Unclassified'),
        ('session_imported_sse_s3_dataset1_tables', 'Official'),
        ('session_imported_kms_s3_dataset1_tables', 'Secret'),
    ],
)

FOLDERS_FIXTURES_PARAMS = (
    'folders_fixture_name',
    [
        'session_s3_dataset1_folders',
        'session_imported_sse_s3_dataset1_folders',
        'session_imported_kms_s3_dataset1_folders',
    ],
)

TABLE_FILTERS_FIXTURES_PARAMS = (
    'tables_fixture_name, table_filters_fixture_name',
    [
        ('session_s3_dataset1_tables', 'session_s3_dataset1_tables_data_filters'),
        ('session_imported_sse_s3_dataset1_tables', 'session_imported_sse_s3_dataset1_tables_data_filters'),
        ('session_imported_kms_s3_dataset1_tables', 'session_imported_kms_s3_dataset1_tables_data_filters'),
    ],
)
