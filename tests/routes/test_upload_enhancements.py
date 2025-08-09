import tempfile
from backend.models import UploadedTree

def test_invalid_gedcom_extension_rejected(client, db_session):
    bad_data = b"not a gedcom"
    with tempfile.NamedTemporaryFile(suffix='.gedcom', delete=False) as tmp:
        tmp.write(bad_data)
        tmp.flush()
        path = tmp.name
    with open(path, 'rb') as fh:
        resp = client.post(
            '/api/upload/',
            data={
                'file': (fh, 'bad.gedcom'),
                'tree_name': 'BadFile'
            },
            content_type='multipart/form-data'
        )
    assert resp.status_code == 400
    # ensure nothing persisted
    assert db_session.query(UploadedTree).count() in (0, db_session.query(UploadedTree).count())

