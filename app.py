from flask import Flask,jsonify,request,Response,render_template

from wit import Wit

app = Flask(__name__)
access_token = 'PQWCP34JWQI3KFAGX3IJGZBDH7JN66LM'

@app.route('/')
def main():
    return "welcome to memorAi"

@app.route('/test')
def botTest():
    return render_template('test.html')

#add api calls here.start with '/api'
@app.route('/api/chatbot/<message>')
def chatbot(message):
    client = Wit(access_token)
    bot_response = client.message(message)
    entity = bot_response['entities']
    intent = ''
    sentiment = ''
    if bot_response['intents']:
        intent = bot_response['intents'][0]['name']
    if bot_response['traits'] and bot_response['traits']['wit$sentiment']:
        sentiment = bot_response['traits']['wit$sentiment'][0]['value']
    chat_response = 'Hmm..'
    if intent == 'get_name':
        #todo db call
        name = 'joe'
        chat_response = 'Haha your name is '+name+'\n Hello '+name+'!'
    
    elif intent == 'get_contact':
        #todo db call
        contact = '+916969696969'
        chat_response = 'Your emergency contact is '+contact+' take care.'

    elif intent == 'get_medicine':
        #todo db call
        medicine = [['2pm','crocin'],['3pm','sleeping pills']]
        chat_response = ''
        for i in medicine:
            chat_response+= medicine[1]+' at '+medicine[0]
        if chat_response:
            chat_response = 'Your medicines listed for today are:\n' + chat_response
        else:
            'no medicines listed!'
    elif intent == 'get_address':
        #todo db call
        address = '12th street oxford street'
        chat_response = 'You live at '+address
    
    elif sentiment == 'negative':
        chat_response = 'Oh no :( Things are going to get better. Wanna talk to someone?'
    
    response = dict()
    response['bot_response'] = bot_response
    response['chat_response'] = chat_response
    
    return response

#comment below call for local setup
if __name__ == '__app__':
    app.run(port=5000) 

#Uncomment this for local run
#app.run(port=5000)  

