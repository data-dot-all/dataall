import os
import pytest

checkov_scan = pytest.mark.skipif(
    os.getenv('CHECKOV_ACTIONS', 'false') != 'true', reason='Pytest used for Checkov Scan CDK Synth Output'
)
