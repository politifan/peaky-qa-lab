"""A worked test. Write your own submission; this file is a reading example."""
def test_quantity_edges(client,make_data):
    before=client.get('/bookings',params={'owner':'boundary-example'}).json()
    for qty in [0,6]:
        response=client.post('/bookings',json=make_data(owner='boundary-example',quantity=qty))
        assert response.status_code==422
    assert client.get('/bookings',params={'owner':'boundary-example'}).json()==before
    for qty in [1,5]:
        response=client.post('/bookings',json=make_data(owner='boundary-example',quantity=qty))
        assert response.status_code==201
        assert response.json()['quantity']==qty
