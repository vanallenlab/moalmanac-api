import dotenv
import os
import uvicorn

from app.main import create_app

dotenv.load_dotenv(override=False)
app = create_app()


if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = bool(os.environ.get('DEBUG', False))

    uvicorn.run(app="app.main:app", host=host, port=port, reload=True)
