from waitress import serve
from presentation.wsgi import application  # Импортируйте ваше WSGI-приложение

if __name__ == '__main__':
    serve(application, host='localhost', port=8080, threads=4)
