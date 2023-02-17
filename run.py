from app import flask_app, socketio

if __name__ == '__main__':
    socketio.run(flask_app, port=flask_app.config['FLASK_PORT'], host=flask_app.config['FLASK_IP'])

#if started from the commandline:
#venv/bin/uwsgi --http :5000 --gevent 1000 --http-websockets --master  -w run:flask_app --logto log-file