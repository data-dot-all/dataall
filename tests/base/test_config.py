from dataall.base.config import config


def test_config():
    config.set_property('k1', 'v1')
    assert config.get_property('k1') == 'v1'

    assert config.get_property('not_exist', 'default1') == 'default1'

    config.set_property('a.b.c', 'd')
    assert config.get_property('a.b.c') == 'd'
    assert 'c' in config.get_property('a.b')
    assert 'k' not in config.get_property('a.b')
    assert config.get_property('a.b.k', 'default2') == 'default2'
    assert 'b' in config.get_property('a')

    config.set_property('a.b.e', 'f')
    assert config.get_property('a.b.c') == 'd'
    assert config.get_property('a.b.e') == 'f'
