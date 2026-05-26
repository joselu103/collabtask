# main.py
import uvicorn

from src.app import create_app
from src.settings.settings import get_settings


def main():
    settings = get_settings()
    if settings.debug:
        reload = True
        app = "src.app:app"
    else:
        reload = False
        app = create_app()
    uvicorn.run(app=app, host=settings.host, port=settings.port, reload=reload)


if __name__ == "__main__":
    main()
