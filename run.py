# run.py
from dotenv import load_dotenv

load_dotenv()  # .env ファイルを読み込む

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
