

def deploy():
	"""Run deployment tasks."""
	from app import create_app,db,make_celery
	from flask_migrate import upgrade,migrate,init,stamp
	from models import User, Progress

	app = create_app()

	app.app_context().push()
	db.create_all()
	celery = make_celery(app)
	
	# migrate database to latest revision
	# init()
	stamp()
	migrate()
	upgrade()
	
deploy()
	