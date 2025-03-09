# run.py
import argparse
from dotenv import load_dotenv

load_dotenv()  # .env ファイルを読み込む

from app import create_app

app = create_app()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the application')
    parser.add_argument('--port', type=int, default=5005, help='Port to run the application on')
    args = parser.parse_args()
    
    app.run(debug=True, port=args.port)
