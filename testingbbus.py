import random
import datetime
import socket
import gunicorn
import jwt
from flask import Flask, request, jsonify

app = Flask(__name__)
SECRET_KEY = "my_secret_key"

previous_credittransaction_id = None


def token_required(f):
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith("Bearer "):
            return jsonify({"statusCode": "401", "status": "UNAUTHORIZED"}), 401
        
        try:
            token = token.split(" ")[1]
            jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({"statusCode": "401", "status": "UNAUTHORIZED", "message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"statusCode": "401", "status": "UNAUTHORIZED", "message": "Invalid token"}), 401
        
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/authenticate', methods=['POST'])
def authenticate():
    data = request.get_json()
    if not data or "userName" not in data or "password" not in data:
        return jsonify({"response": "001", "responseMesg": "Wrong UserName or Password"}), 400
    
    username = data["userName"]
    password = data["password"]
    
    # Simple check for demonstration
    if username != "brassica" or password != "brassicapwd":
        return jsonify({
            "response": "001",
            "responseMesg": "Wrong UserName or Password"
        })
    
    token_payload = {
        "unique_name": username,
        "UserID": username,
        # Timestamps
        "nbf": datetime.datetime.utcnow().timestamp(),
        "exp": (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).timestamp(),
        "iat": datetime.datetime.utcnow().timestamp()
    }
    
    token = jwt.encode(token_payload, SECRET_KEY, algorithm='HS256')
    ip_address = socket.gethostbyname(socket.gethostname())
    
    return jsonify({
        "response": "000",
        "responseMesg": "Token Generated",
        "data": {
            "resp1": token,
            "resp2": ip_address
        }
    })

@app.route('/DebitMoney', methods=['POST'])
@token_required
def debit_money():
    global previous_credittransaction_id
    data = request.get_json()
    if not data or "transactionId" not in data:
        return jsonify({"statusCode": "400", "status": "BAD_REQUEST", "message": "Missing transaction ID"}), 400
    
    transaction_id = data["transactionId"]
    
    # Duplicate transaction check
    if transaction_id == previous_credittransaction_id:
        return jsonify({
            "statusCode": "417",
            "status": "DUPLICATE",
            "message": "Duplicate Transaction ID.",
            "extralTransactionId": None,
            "transactionId": transaction_id,
            "paymentURL": None
        })
    
    previous_credittransaction_id = transaction_id
    
    # Random response
    random_response = random.choice(["ACCEPTED", "REQUEST_NOT_ACCEPTED"])
    
    if random_response == "REQUEST_NOT_ACCEPTED":
        return jsonify({
            "statusCode": "406",
            "status": "REQUEST_NOT_ACCEPTED",
            "message": "Request not accepted for one or more reasons.",
            "extralTransactionId": str(random.randint(100000000000, 999999999999)),
            "transactionId": transaction_id,
            "paymentURL": None
        })
    
    return jsonify({
        "statusCode": "202",
        "status": "ACCEPTED",
        "message": "Request is being processed",
        "extralTransactionId": str(random.randint(100000000000, 999999999999)),
        "transactionId": transaction_id
    })




    
@app.route('/transStatusQuery', methods=['POST'])
@token_required
def trans_status_query():
    data = request.get_json()
    if not data or "transactionId" not in data:
        return jsonify({"statusCode": "400", "status": "BAD_REQUEST", "message": "Missing transaction ID"}), 400
    
    transaction_id = data["transactionId"]
    
    # Randomly choose a status
    random_response = random.choice(["SUCCESSFUL", "TRANSACTION_NOT_FOUND", "EXPIRED", "FAILED"])
    
    if random_response == "TRANSACTION_NOT_FOUND":
        return jsonify({
            "statusCode": "404",
            "status": "TRANSACTION_NOT_FOUND",
            "message": "Transaction not found.",
            "institutionApprovalCode": "000000000000",
            "transactionId": transaction_id,
            "extralTransactionId": None,
            "reason": None
        })
    elif random_response == "EXPIRED":
        return jsonify({
            "statusCode": "409",
            "status": "EXPIRED",
            "message": "Request Expired",
            "institutionApprovalCode": "000000000000",
            "transactionId": transaction_id,
            "extralTransactionId": str(random.randint(100000000000, 999999999999)),
            "reason": None
        })
    elif random_response == "FAILED":
        return jsonify({
            "statusCode": "424",
            "status": "FAILED",
            "message": "LOW_BALANCE_OR_PAYEE_LIMIT_REACHED_OR_NOT_ALLOWED",
            "institutionApprovalCode": "000000000000",
            "transactionId": transaction_id,
            "extralTransactionId": str(random.randint(100000000000, 999999999999)),
            "reason": None
        })
    
    return jsonify({
        "statusCode": "200",
        "status": "SUCCESSFUL",
        "message": "Request processed successfully.",
        "institutionApprovalCode": str(random.randint(100000, 999999)),
        "transactionId": transaction_id,
        "extralTransactionId": str(random.randint(100000000000, 999999999999)),
        "reason": None
    })

@app.route('/getBalance', methods=['POST'])
@token_required
def get_balance():
    """
    Simulates retrieving an account balance.
    Returns a JSON with a randomly generated balance between 1 and 1000
    and a timestamp in DD-MM-YYYY HH:MM:SS format.
    """
    # Generate a random account balance
    balance = format(random.uniform(1, 1000), '.4f')
    date_time = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    
    return jsonify({
        "accountBalance": balance,
        "dateTime": date_time
    })

@app.route('/nameEnquiry', methods=['POST'])
@token_required
def name_enquiry():
    """
    Simulates a name inquiry request. 
    1 out of 5 times, it returns an ACCOUNT_NOT_FOUND error.
    Otherwise, it returns a success response with a random name.
    """
    data = request.get_json()
    if not data or "transactionId" not in data or "accountNumber" not in data:
        return jsonify({"statusCode": "400", "status": "BAD_REQUEST", "message": "Missing parameters"}), 400
    
    transaction_id = data["transactionId"]
    account_number = data["accountNumber"]
    
    # 1/5 chance of "ACCOUNT_NOT_FOUND"
    if random.randint(1, 5) == 1:
        return jsonify({
            "statusCode": "419",
            "status": "ACCOUNT_NOT_FOUND",
            "message": "Account not found.",
            "accountName": "",
            "accountNumber": "",
            "transactionId": "",
            "institutionApprovalCode": None,
            "extralTransactionId": str(random.randint(100000000000, 999999999999))
        })
    
    # Random list of possible account names
    account_names = [
        "JONATHAN AMPONSAH", "BRIGHT OSEI", "LINDA MENSAH", "MERCY TAYLOR", "KWABENA BOATENG",
        "AMA SERWAA", "PHILIP COLE", "REBECCA ADDAI", "GEORGE MENSAH", "MICHAEL DJAN",
        "SAMUEL KWAKU", "ABIGAIL YEBOAH", "MARY ASARE", "STEPHEN APPIAH", "FELICIA NKRUMAH",
        "AUDREY ANTWI", "DANIEL ADOM", "PRISCILLA NTIM", "BENJAMIN AMOAH", "RITA KWASI"
    ]
    
    # Select a random name from the list
    chosen_name = random.choice(account_names)
    
    return jsonify({
        "statusCode": "200",
        "status": "SUCCESSFUL",

        "message": "Request processed successfully",
        "accountName": chosen_name,
        "accountNumber": account_number,
        "transactionId": transaction_id,
        "institutionApprovalCode": "0000000",
        "extralTransactionId": str(random.randint(100000000000, 999999999999))
    })

@app.route('/sendMoney', methods=['POST'])
@token_required
def send_money():
    data = request.get_json()
    required_fields = ["channel", "institutionCode", "accountNumber", "accountName", "amount", "creditNaration", "transactionId"]
    
    if not data or any(field not in data for field in required_fields):
        return jsonify({"statusCode": "400", "status": "BAD_REQUEST", "message": "Missing transaction ID"}), 400
    
    transaction_id = data["transactionId"]
    extral_transaction_id = str(random.randint(10000000, 99999999))
    
    return jsonify({
        "statusCode": "202",
        "status": "ACCEPTED",
        "message": "Request is being processed",
        "extralTransactionId": extral_transaction_id,
        "transactionId": transaction_id
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000,debug=False)