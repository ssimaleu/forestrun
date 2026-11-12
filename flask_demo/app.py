from flask import Flask, render_template

app = Flask(__name__)

STUDENT_ID = "326020080"


@app.route("/")
def index():
    return render_template("index.html", title="hands-on 1", student_id=STUDENT_ID)


if __name__ == "__main__":
    # host="0.0.0.0" makes the app accessible from other devices on your network,
    # reachable at http://<your-ip-address>:8000
    app.run(host="0.0.0.0", port=8000, debug=True)
