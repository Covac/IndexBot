from flask import Flask, request, send_from_directory,jsonify, Response
from headers import staticSessionHeader as sHeader
from functions import inspectUserProfile, getArticleComments, getReplies, getIP
from options import Logging
from config import dbPath, accountAmount
import DbHandler
import CardanoFuncs
import secrets
import string
#from aioflask import ... || pip install flask[async],aioflask
#https://stackoverflow.com/questions/70321014/runtimeerror-install-flask-with-the-async-extra-in-order-to-use-async-views
#More testing for stability
"""
Payload examples:
{
    "action": "React",
    "actionType": 0,
    "targetId": 4904024,
    "targetPublicId": "vJGPkD51aP",
    "amount": 44,
    "apiKey": "What's default?"
}

{
    "action": "React",
    "actionType": 1,
    "targetId": 4904024,
    "targetPublicId": "vJGPkD51aP",
    "amount": 16,
    "apiKey": "What's default?"
}

{
    "action": "Nuke",
    "actionType": 0,
    "targetId": 4904024,
    "targetPublicId": "vJGPkD51aP",
    "amount": 10,
    "apiKey": "What's default?"
}
"""

def getApp(pipe):
    app = Flask(__name__, static_url_path='/assets', static_folder='../IndexBotBrowser/dist/assets' )
    db_handler = DbHandler.DatabaseHandler(dbPath)

    @app.route('/api', methods=['POST'])
    def handle_api():#we can use async extra flask?
        #verify and do
        try:
            data = request.json#we need nicer data!
            #actionType,action,targetId,targetPublicId,relatedArticleURL,amount,apiKey=data.values()
            #SOMETHING WENT WRONG WITH ORDER 
            actionType = data['actionType']
            action = data['action']
            targetId = data['targetId']
            targetPublicId = data['targetPublicId']
            relatedArticleURL = data['relatedArticleURL']
            amount = data['amount']
            apiKey = data['apiKey']
                #assert types
            #return {'Error':'Invalid request data'}, 400, {"Content-Type":"application/json"}
            #validate key
            if not apiKey.isalnum():
                return jsonify({'Error':'Invalid API key'}), 400#, {"Content-Type":"application/json"}
            #validate transaction
            token_amount = db_handler.get_token_amount(apiKey)
            if token_amount == None:
                return jsonify({'Error':'Insufficient funds!'}), 403#, {"Content-Type":"application/json"}
            #calculate cost || should be based on the number of bots available
            if action == 'Nuke':
                cost = int(amount) * 100
            elif action == 'React':
                cost = int(amount) * 1
            if token_amount < cost:
                return jsonify({'Error':'Insufficient funds!'}), 403#, {"Content-Type":"application/json"}
            db_handler.update_token_amount(apiKey,-cost)
            #Make sure we get real ip, it could be forwarded
            IP = getIP(request)
            db_handler.add_transaction(apiKey,action,-cost,IP)
            print(action,actionType,targetId,targetPublicId,amount,apiKey, flush=True)#DEL ME
            if action == 'Nuke':
                userURL = f"https://www.index.hr/profil/{targetPublicId}"
                pipe.send([action.lower(),[userURL,0,amount]])
            elif action == 'React':
                pipe.send([str(action.lower()),[str(targetId),str(actionType)],[amount,relatedArticleURL]])
                print("this is away, ",[str(action.lower()),[str(targetId),str(actionType)],[amount,relatedArticleURL]], flush=True)
            #mess = pipe.recv()
            #print(mess)
            return jsonify({'Response':'success','newBalance':token_amount-cost}), 200#, {"Content-Type":"application/json"}
        except Exception as e:#Multiple exceptions later, surely!
            print(e, flush=True)
            return e, 400#, {"Content-Type":"application/json"}
        
    @app.route('/api/balance', methods=['POST'])#Its etiquette to send api keys in stuff like this
    def api_balance():
        try:
            data = request.json
            apiKey = data['apiKey']
            if not apiKey.isalnum():
                return jsonify({'Error':'Invalid API key'}), 400#, {"Content-Type":"application/json"}
            token_balance = db_handler.get_token_amount(apiKey)
            return jsonify({'Response':'success','tokenBalance':token_balance}), 200
        except Exception as e:
            print(e, flush=True)
            return jsonify(e), 400
        
    @app.route('/api/online', methods=['GET'])
    def online():#I am not doing some crazy process communication just to get one number
        #nor am I gonna risk some race condition trying to open the same accounts.txt file
        return jsonify({'Online':accountAmount}), 200

        
    @app.route('/', methods=['GET'])
    def test_response():
        return send_from_directory('../IndexBotBrowser/dist','index.html')
    
    @app.route('/api/proxy', methods=['GET'])  # Define the route for the proxy
    def proxy():
        try:#handle proxy
            # Get the URL to proxy from the query parameters
            url = request.args.get('url')
            urlType = request.args.get('type')
            skip = int(request.args.get('skip'))
            if Logging.DEBUG:
                print(urlType)
                print(url)
                print(request.headers)
                print(request.data)
                #TRIM DOWN RESPONSES TO ONLY USEFUL STUFF, THEN WE DO
                #FRONTEND TO DO ON DEMAND COMMENTS
            if not url:
                return jsonify({'error': 'URL parameter is missing'}), 400
            if urlType == 'profile':
                comments = inspectUserProfile(url,10+skip,True,skip)
                return jsonify(comments), 200
            elif urlType == 'article':
                comments = getArticleComments(url,0+skip,10+skip)
                return jsonify(comments), 200#supstitute this
            else:
                return jsonify({'error': 'TYPE parameter is missing'}), 400

        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
    @app.route('/api/replies', methods=['GET'])
    def replies():
        try:
            cid = request.args.get('commentId')
            take = request.args.get('take', 5)
            if not cid:
                return jsonify({'error': 'No commentId provided!'}), 400
            else:
                replies = getReplies(int(cid), skip=0, take=int(take))
                return jsonify(replies), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
    #====================== TRANSACTION ==========================
        
    @app.route('/api/order', methods=['POST'])
    def order():
        data = request.json
        IP = getIP(request)
        apiKey,sessionKey,requestIP = data['apiKey'],data['sessionKey'], IP
        print(apiKey,sessionKey,requestIP)
        if not apiKey.isalnum():
            return jsonify({'Error':'API Key must be alphanumeric!'}), 400
        if db_handler.check_order_exists(sessionKey):
            return jsonify({'Error':'Session key already exists'}), 400
        a,b,c = CardanoFuncs.generate_payment_address()
        print(a,b,c,flush=True)
        db_handler.add_payment_address(a,str(b),str(c))
        db_handler.add_order(apiKey,sessionKey,a,requestIP)
        return jsonify({'Status': 'SUCCESS', 'PaymentAddress':a}), 200
    
    @app.route('/api/order/confirmTransaction', methods=['POST'])
    def confirmation():#at this point isn't session key useless?
        data = request.json
        IP = getIP(request)
        session_key = data['sessionKey']
        apikey,paymentAddr,status = db_handler.get_apikey_addr_from_order(session_key)
        if status == 'COMPLETED':
            return jsonify({'Result':'Failed','Reason':'You already completed this transasction'}), 200
        balance = CardanoFuncs.get_cardano_balance_cardanoscan(paymentAddr)
        #testing only
        #balance = CardanoFuncs.get_addr_preview_balance(paymentAddr) #TESTING FUNCTION
        if balance >= 2000000:#Minimum transaction value for us!
            #add checks for already present apikeys, to only add balance
            tokens = CardanoFuncs.calculate_ADA_to_tokens(balance,CardanoFuncs.get_cardano_price(),2)
            if not(db_handler.check_apikey_exists(apikey)):
                db_handler.add_api_key(apikey)
            db_handler.update_token_amount(apikey,tokens)
            db_handler.add_transaction(apikey,'TOKEN PURCHASE',tokens,IP)
            db_handler.confirm_order(balance,'COMPLETED',apikey,session_key,IP)
            return jsonify({'Result':'Completed','TokensBought':tokens}), 200
        elif balance == 0:#nobody paid yet!
            return jsonify({'Result':'Failed','Reason':'Transaction not detected yet! Try again later when this message disappears.'}), 200
        else:
            return jsonify({'Result':'Failed','Reason':'Transaction amount is under minimum required, are you okay? Send more to confirm!'}), 200
        
    @app.route('/api/session', methods=['GET'])
    def session(complexity=16):
        session_token = secrets.token_hex(16)
        return jsonify({'SessionToken':session_token}), 200
    
    @app.route('/api/generatekey', methods=['GET'])
    def generateAPIKey(length=32):
        charset = string.ascii_letters + string.digits
        apikey = ''.join(secrets.choice(charset) for _ in range(length))
        return jsonify({'generatedAPIKey':apikey})

    return app,db_handler