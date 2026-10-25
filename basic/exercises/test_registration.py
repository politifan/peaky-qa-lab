from registration import allowed
def test_lower_edge():
    assert allowed(14) is True
    assert allowed(13) is False
    assert allowed(True) is False
