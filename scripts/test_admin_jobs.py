from app import create_app

app = create_app()
client = app.test_client()
resp = client.get('/admin/jobs')
print('STATUS', resp.status_code)
print(resp.get_data(as_text=True))
