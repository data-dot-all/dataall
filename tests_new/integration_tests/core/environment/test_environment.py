from assertpy import assert_that


def test_create_env(session_env1):
    assert_that(session_env1.stack.status).is_equal_to('CREATE_COMPLETE')


def test_create_env2(session_env2):
    assert_that(session_env2.stack.status).is_equal_to('CREATE_COMPLETE')
