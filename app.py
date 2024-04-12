from flask import Flask, render_template
from socket import gethostname

app = Flask(__name__, instance_relative_config=True)

# Functions used in app go here
def main():
    pass


# ----- START

# Home page for website
@app.route("/")
def home():
    return render_template("index.html")


# ----- END
if __name__ == '__main__':
    main()
    # If statement to prevent run when hosting in PythonAnywhere
    if 'liveconsole' not in gethostname():
        app.run() # app.run(debug=True, port = 8000) to set different port