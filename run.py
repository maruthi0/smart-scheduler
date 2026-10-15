from dotenv import load_dotenv

load_dotenv()  # read SECRET_KEY etc. from .env before the app is configured

from app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    app.run()  # debug mode comes from FLASK_DEBUG in .env
