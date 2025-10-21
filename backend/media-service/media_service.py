from app import create_app
app = create_app()

@app.route("/favicon.ico")
def favicon():
    return "", 204

if __name__ == "__main__":
    app.run(host=app.config['SERVER_HOST'], port=app.config['SERVER_PORT'])
