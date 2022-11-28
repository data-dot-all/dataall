def test_fine(db):
    assert True


def test_app(app):
    print(app)


def test_client(client):
    response = client.query(
        """ query Up {
            up {
                _ts
                message
                username
                groups
            }
        }"""
    )
    assert response.data.up.message == "server is up"
    response = client.query(
        """query Up {
            up{
                _ts
                message
                username
                groups
            }
        }""",
        username="testuser",
    )
    assert response.data.up.message == "server is up"
    assert response.data.up.username == "testuser"

    response = client.query(
        """query Up {
            up {
                _ts
                message
                username
            groups
            }
        }""",
        username="testuser",
        groups=["a", "b"],
    )
    assert response.data.up.message == "server is up"
    assert response.data.up.username == "testuser"
    assert str(response.data.up.groups) == str(["a", "b"])

    response = client.query(
        """query Up ($arg:String){
            up (arg:$arg){
                _ts
                message
                username
                groups
                arg
            }
        }""",
        username="testuser",
        groups=["a", "b"],
        arg="argument1",
    )
    assert response.data.up.message == "server is up"
    assert response.data.up.username == "testuser"
    assert str(response.data.up.groups) == str(["a", "b"])
    assert str(response.data.up.arg) == "argument1"
