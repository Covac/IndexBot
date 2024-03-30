from flask import Flask, request, send_from_directory,jsonify
from headers import staticSessionHeader as sHeader
from functions import inspectUserProfile,getArticleComments
from config import dbPath
import DbHandler
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
            action,actionType,targetId,targetPublicId,amount,apiKey=data.values()
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
            db_handler.add_transaction(apiKey,action,amount,request.remote_addr)
            print(action,actionType,targetId,targetPublicId,amount,apiKey, flush=True)#DEL ME
            if action == 'Nuke':
                userURL = f"https://www.index.hr/profil/{targetPublicId}"
                pipe.send([action.lower(),[userURL,0,amount]])
            elif action == 'React':
                pipe.send([str(action.lower()),[str(targetId),str(actionType)],[amount]])
                print("this is away, ",[str(action.lower()),[str(targetId),str(actionType)],[amount]], flush=True)
            #mess = pipe.recv()
            #print(mess)
            return jsonify({'response':'success','newBalance':'INFINITY'}), 200#, {"Content-Type":"application/json"}
        except Exception as e:#Multiple exceptions later, surely!
            print(e, flush=True)
            return e, 400#, {"Content-Type":"application/json"}
        
    @app.route('/', methods=['GET'])
    def test_response():
        return send_from_directory('../IndexBotBrowser/dist','index.html')
    
    @app.route('/api/proxy', methods=['GET'])  # Define the route for the proxy
    def proxy():
        try:#handle proxy
            # Get the URL to proxy from the query parameters
            url = request.args.get('url')
            urlType = request.args.get('type')
            print(urlType)
            print(url)
            print(request.headers)
            print(request.data)
            #TRIM DOWN RESPONSES TO ONLY USEFUL STUFF, THEN WE DO 
            #FRONTEND TO DO ON DEMAND COMMENTS
            if not url:
                return jsonify({'error': 'URL parameter is missing'}), 400
            if urlType == 'profile':
                comments = inspectUserProfile(url,10,True)
                return jsonify(comments), 200
            elif urlType == 'article':
                comments = getArticleComments(url,0,10)
                return jsonify(comments), 200#supstitute this
            else:
                return jsonify({'error': 'TYPE parameter is missing'}), 400

        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return app,db_handler