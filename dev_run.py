from app import create_app

app = create_app(config_path='config.ini')

if __name__ == '__main__':
    app.run('localhost', port=8000, debug=True)
