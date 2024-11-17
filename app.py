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

@app.route('/insurance')
def insurance():
    return render_template("insurance.html")

@app.route('/banking', methods=['GET', 'POST'])
def banking():
    # Retrieve user info from the session
    name = session.get('name', 'Guest')
    checking_balance = session.get('checking_balance', 1250.00)  # Default balance
    savings_balance = session.get('savings_balance', 500.00)  # Default balance
    transactions = session.get('transactions', [])  # Default empty transaction history

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'payment':
            amount = request.form.get('amount')
            try:
                amount = float(amount)
            except ValueError:
                return "Invalid amount format", 400

            from_account = request.form.get('from-account')
            recipient = request.form.get('recipient')
            
            # Handle payment (subtract from the selected account)
            if from_account == 'checking':
                if checking_balance >= amount:
                    checking_balance -= amount
                    transactions.append(f"{recipient}: -${amount}")
                else:
                    return "Insufficient funds in Checking Account", 400
            elif from_account == 'savings':
                if savings_balance >= amount:
                    savings_balance -= amount
                    transactions.append(f"{recipient}: -${amount}")
                else:
                    return "Insufficient funds in Savings Account", 400

        elif action == 'transfer':
            transfer_amount = request.form.get('transfer-amount')
            try:
                transfer_amount = float(transfer_amount)
            except ValueError:
                return "Invalid transfer amount format", 400

            from_account = request.form.get('from-account')
            to_account = request.form.get('to-account')

            if from_account == 'checking':
                if checking_balance >= transfer_amount:
                    checking_balance -= transfer_amount
                    if to_account == 'checking':
                        transactions.append(f"To Checking: +${transfer_amount}")
                    elif to_account == 'savings':
                        savings_balance += transfer_amount
                        transactions.append(f"To Savings: +${transfer_amount}")
                    elif to_account == 'external':
                        bank_name = request.form.get('bank-name')  # Get the external bank name
                        transactions.append(f"External Bank ({bank_name}): -${transfer_amount}")
                else:
                    return "Insufficient funds in Checking Account", 400

            elif from_account == 'savings':
                if savings_balance >= transfer_amount:
                    savings_balance -= transfer_amount
                    if to_account == 'savings':
                        transactions.append(f"To Savings: +${transfer_amount}")
                    elif to_account == 'checking':
                        checking_balance += transfer_amount
                        transactions.append(f"To Checking: +${transfer_amount}")
                    elif to_account == 'external':
                        bank_name = request.form.get('bank-name')  # Get the external bank name
                        transactions.append(f"External Bank ({bank_name}): -${transfer_amount}")
                else:
                    return "Insufficient funds in Savings Account", 400

        # Store updated balances and transactions in the session
        session['checking_balance'] = checking_balance
        session['savings_balance'] = savings_balance
        session['transactions'] = transactions

        # Redirect back to banking page with updated info
        return redirect(url_for('banking'))

    return render_template("banking.html", name=name, checking_balance=checking_balance,
                           savings_balance=savings_balance, transactions=transactions)

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    session['name'] = name  # Store the name in the session
    session['checking_balance'] = 1250.00  # Default balance for checking
    session['savings_balance'] = 500.00    # Default balance for savings
    session['transactions'] = []           # Empty transaction history
    return redirect(url_for('banking'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    name = email.split('.')[0].capitalize()
    session['name'] = name  # Store the name in the session
    session['checking_balance'] = 1250.00  # Default balance for checking
    session['savings_balance'] = 500.00    # Default balance for savings
    session['transactions'] = []           # Empty transaction history
    return redirect(url_for('banking'))

if __name__ == '__main__':
    app.run(debug=True)
