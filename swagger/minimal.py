import connexion

app = connexion.FlaskApp(__name__, specification_dir='./')
app.add_api('swagger.yaml', arguments={'title': 'Your API Title'})
app.run(port=8080)
