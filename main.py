# main.py
import uvicorn

from src.app import create_app

development_mode = True  # TODO temporary


def main():
    if development_mode:
        reload = True
        app = "src.app:app"
    else:
        reload = False
        app = create_app()
    uvicorn.run(app=app, host="localhost", port=8000, reload=development_mode)


if __name__ == "__main__":
    main()
