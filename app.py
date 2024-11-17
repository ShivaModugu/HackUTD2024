from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for sessions

@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")

@app.route('/onboarding')
def onboarding():
    return render_template("onboarding.html")

@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/banking', methods=['GET'])
def banking():
    name = session.get('name', 'Guest')  # Retrieve name from session or default to 'Guest'
    return render_template("banking.html", name=name)

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    session['name'] = name  # Store the name in the session
    return redirect(url_for('banking'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    name = email.split('.')[0].capitalize()
    session['name'] = name  # Store the name in the session
    return redirect(url_for('banking'))

if __name__ == '__main__':
    app.run(debug=True)
