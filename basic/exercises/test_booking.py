from booking import reserve
def test_remaining():
    assert reserve(2,2)==0
    assert reserve(2,-1)==2
    assert reserve(2,3)==2
