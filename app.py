from flask import Flask, render_template

# Initialize the Flask app
app = Flask(__name__)

# Define a route
@app.route('/')
@app.route('/index.html')
def index():
    return render_template("index.html")

@app.route('/onboarding.html')
def onboarding():
    return render_template("onboarding.html")

@app.route('/home.html')
def home():
    return render_template("home.html")

@app.route('/banking.html')
def banking():
    return render_template("banking.html")

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
