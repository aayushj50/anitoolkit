from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "⚙️ AniToolkit is loading… check back soon!"

if __name__ == "__main__":
    app.run(debug=True)
