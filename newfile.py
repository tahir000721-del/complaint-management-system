from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <html>
    <head>
        <title>Complaint Management System</title>
    </head>
    <body>
        <h1>Complaint Management System</h1>
        <h2>Welcome</h2>
        <p>System is working successfully!</p>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)