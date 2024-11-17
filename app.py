import re
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import openai
import json
from decimal import Decimal


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for sessions
results = {}

# Initialize the OpenAI client
client = openai.OpenAI(
    api_key="81515365-a441-4726-8b1a-5401c5ea51a3",
    base_url="https://api.sambanova.ai/v1",
)

# Function to send a message to the chatbot and get a response
def chat_with_assistant(user_message, quiz_data):
    response = client.chat.completions.create(
        model='Meta-Llama-3.1-8B-Instruct',
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Here is some quiz data:" + str(quiz_data) +  "in a dictionary format to interpret for the user"},
            {"role": "user", "content": user_message}
        ],
        temperature=0.1,
        top_p=0.1
    )
    return response.choices[0].message.content

def load_quiz_data():
    with open('quiz_results.json', 'r') as file:
        return json.load(file)

# Function to handle insurance-related questions
@app.route('/send-query', methods=['POST'])
def send_query():
    data = request.get_json()
    user_question = data.get('question')
    
    # Load the quiz data once per request
    quiz_data = load_quiz_data()
    
    if user_question:
        assistant_response = chat_with_assistant(user_question, quiz_data)
        return jsonify({'response': assistant_response})
    else:
        return jsonify({'error': 'No question provided'}), 400

def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',       # Replace with your database host
        user='root',       # Replace with your database username
        password='7635Yearling!', # Replace with your database password
        database='hackathon_db',
        port=3306  # Replace with your database name
    )
    return connection

def parse_answers(array):
    # Initialize conditions for each category
    conditions = {
        'Additional': None,
        'PaymentStructure': None,
        'CoverageType': None,
        'PremiumRange': None
    }

    # Define mappings based on the answer choices

    # Payment Structure (e.g., 'B' or 'A')
    if 'A.' in array[0]:
        conditions['Additional'] = ""
    elif 'B.' in array[0]:
        conditions['Additional'] = "IC.CompanyID IN (SELECT CompanyID FROM InsurancePlans GROUP BY CompanyID HAVING COUNT(PlanID) > 1)"
    elif 'C.' in array[0]:
        conditions['Additional'] = "IC.Review > 4.0"
    
    if 'B.' in array[1]:  # Higher monthly premiums with lower out-of-pocket costs
        conditions['PaymentStructure'] = "IP.PaymentStructure = 'Higher Monthly'"
        conditions['OutOfPocketCost'] = "IP.OutOfPocketCost = 'Low'"
    elif 'A.' in array[1]:  # Affordable premiums (default if needed)
        conditions['PaymentStructure'] = "IP.PaymentStructure = 'Lower Monthly'"
        conditions['OutOfPocketCost'] = "IP.OutOfPocketCost = 'High'"
    elif 'C.' in array[1]:
        conditions['PaymentStructure'] = "IP.PaymentStructure = 'Flexible'"
        conditions['OutOfPocketCost'] = "IP.OutOfPocketCost = 'Flexible'"

    # Risk Type (e.g., 'D' for property insurance)
    if 'D.' in array[2]:  # Property damage or liability (property insurance)
        conditions['CoverageType'] = "PC.CoverageType = 'Property'"
    elif 'C.' in array[2]:  # Health insurance (if we had such an entry)
        conditions['CoverageType'] = "PC.CoverageType = 'Auto'"
    elif 'B.' in array[2]:  # Property damage or liability (property insurance)
        conditions['CoverageType'] = "PC.CoverageType = 'Life'"
    elif 'A.' in array[2]:  # Health insurance (if we had such an entry)
        conditions['CoverageType'] = "PC.CoverageType = 'Health'"

    # Income Range (e.g., "$50,000–$75,000")
    income_match = re.search(r"\$\d{1,3}(?:,\d{3})*–\$\d{1,3}(?:,\d{3})*", array[3])  # Detecting the income range
    budget_match = re.search(r"Less\s+than\s+(\d{1,2})%\s+of\s+annual\s+income", array[4])  # Detecting the budget percentage range
    if income_match and budget_match:
        upper = income_match.group(0).split('–')[1]  # Get the upper value (after the "–")
        
        # Get the percentage value from the budget match
        upper_percentage = int(budget_match.group(1))  # Extract the percentage value
        
        # Parse the upper income value into an integer (remove '$' and ',' symbols)
        upper_value = int(upper.replace('$', '').replace(',', ''))
        
        # Calculate the upper premium value based on the upper percentage
        upper_premium = upper_value * (upper_percentage / 100)  # Apply the upper percentage for the upper bound
        
        # Construct the premium range condition for only the upper value
        conditions['PremiumRange'] = f"IP.PremiumMonthly <= {upper_premium}"

    # Construct the WHERE clause dynamically
    where_clauses = []

    for key, condition in conditions.items():
        if condition:
            where_clauses.append(condition)

    # Join the WHERE clauses with AND
    where_condition = " AND ".join(where_clauses)

    # Construct the final SQL query
    sql_query = f"""
    SELECT 
        IC.CompanyName, 
        IC.PhoneNumber, 
        IC.Email, 
        IC.Review, 
        IC.WebsiteURL, 
        IP.PlanName, 
        IP.PremiumMonthly, 
        IP.OutOfPocketCost, 
        IP.PaymentStructure, 
        IP.BudgetPercentage, 
        PC.CoverageType
    FROM 
        InsuranceCompanies IC
    JOIN 
        InsurancePlans IP ON IC.CompanyID = IP.CompanyID
    JOIN 
        PlanCoverage PC ON IP.PlanID = PC.PlanID
    WHERE 
        {where_condition}
    ORDER BY 
        IC.CompanyName, IP.PlanName, PC.CoverageType
    LIMIT 3;
    """
    
    return sql_query

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

@app.route('/insurance_companies')
def insurance_companies():
    global results
    return render_template("insurance_companies.html", results=results)


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
        session['checking_balance'] = round(checking_balance, 2)
        session['savings_balance'] = round(savings_balance, 2)
        session['transactions'] = transactions

        # Redirect back to banking page with updated info
        return redirect(url_for('banking'))

    return render_template("banking.html", name=name, checking_balance=checking_balance,
                           savings_balance=savings_balance, transactions=transactions)
                           
def transform_to_ordinary_dict(data):
    # Iterate through each dictionary and convert Decimal values to float
    for entry in data:
        for key, value in entry.items():
            if isinstance(value, Decimal):
                entry[key] = float(value)
    return data

@app.route('/submit-quiz', methods=['POST'])
def submit_quiz():
    global results
    # Get the JSON data from the request
    data = request.get_json()
    
    # Get the selected answers from the request
    selected_answers = data.get('answers')
    query = parse_answers(selected_answers)
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)  # Use dictionary to get results as a dictionary
    cursor.execute(query)
    
    # Fetch all results from the query
    results = cursor.fetchall()
    ordinary_data = transform_to_ordinary_dict(results)
    
    # Dump the results into a JSON file
    with open('quiz_results.json', 'w') as file:
        json.dump(ordinary_data, file, indent=4)

    # Close the cursor and connection
    cursor.close()
    connection.close()
    # Return a response (optional)
    return render_template('insurance_companies.html', results=results)

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    session['name'] = name  # Store the name in the session
    session['checking_balance'] = 1250.00  # Default balance for checking
    session['savings_balance'] = 500.00    # Default balance for savings
    session['transactions'] = []           # Empty transaction history
    return redirect(url_for('banking'))

@app.route('/login', methods=['POST', 'GET'])
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
