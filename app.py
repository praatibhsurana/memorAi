from flask import Flask,jsonify,request,Response,render_template,send_file
from wit import Wit
import os
import json
import pyrebase
import config as secrets
from utils import FaceWithAzure
from geopy.geocoders import Nominatim
app = Flask(__name__)

#wit.ai bot
access_token = secrets.WIT_ACCESS_TOKEN

# Temporary list to store reminders
# Initialize Firestore DB
config = secrets.FIREBASE_CONFIG
firebase = pyrebase.initialize_app(config)
db = firebase.database()

def get_address_from_coordinates(coor):
    locator = Nominatim(user_agent="myGeocoder")
    location = locator.reverse(coor)
    print(coor)
    print(location,type(location))
    return str(location)

@app.route('/loctest')
def loctest():
    data = db.child('users').child('789').get()
    data = dict(data.val())
    coor = str(data['patient_location']['loc'])+", "+str(data['patient_location']['lat'])
    ans = get_address_from_coordinates(coor)
    return {'ans':ans}

@app.route('/')
def main():
    return render_template('index.html')

@app.route('/api/createUser',methods = ['POST'])
def createUser():    
    data = request.json
    pno = data['emergency_pno']
    coor = str(data['patient_location']['loc'])+", "+str(data['patient_location']['lat'])
    address = get_address_from_coordinates(coor)
    data['address'] = address
    db.child('users').child(pno).set(data)
    relative_group = FaceWithAzure(pno)
    relative_group.create_group()

    return Response({'status':'success'})

@app.route('/api/get_auth_info/<number>')
def getAuthInfo(number):
    try:
        user = {}
        user = db.child('users').child(number).get()
        d = dict(user.val())
        return jsonify({'user':d})
    except Exception as e:
        print(e)
        return jsonify({'user':str()})

@app.route('/api/set_medicine/<number>',methods = ['POST'])
def update_medicines(number):
    data = request.json
    print(data)
    db.child('users').child(number).update({"medicines": data['data']})
    return Response({'status':'success'}) 

@app.route('/api/add_relative/<number>',methods = ['POST'])
def sync_relative_azure(number):
    data = request.json
    print(data)
    print(number)
    relative_group = FaceWithAzure(number)
    print("here")
    person_id = relative_group.create_person(name = data['name'],user_data=data['relation'])
    relative_group.add_image_to_person(person_id,data['patient_dp'])
    relative_group.train_group()
    return Response({'status':'success'}) 

@app.route('/download/apk')
def download_apk():
    return send_file('memorai.apk',as_attachment=True)

@app.route('/api/check_face/<number>',methods = ['POST'])
def check_face(number):
    print('here')
    try:
        data = request.json
        relative_group = FaceWithAzure(number)
        
        face_id = relative_group.detect_face(data['detect_url'])

        print('faceid',face_id)
        if(face_id != None):
            person_id = relative_group.person_identify(face_id)
            response = relative_group.person_info(person_id)
            return {'status':'success','response' : response}
        return {'status':'error'}
    except Exception as e:
        print(e)
        return {'status':'error'}

@app.route('/api/set_relative/<number>',methods = ['POST'])
def update_relatives(number):
    data = request.json
    print(data)
    db.child('users').child(number).update({"relatives": data['data']})
    return Response({'status':'success'}) 

@app.route('/test')
def botTest():
    return render_template('test.html')

#add api calls here.start with '/api'
@app.route('/api/chatbot/<number>/<message>')
def chatbot(number,message):
    client = Wit(access_token)
    bot_response = client.message(message)
    entity = bot_response['entities']
    per = dict(db.child('users').child(number).get().val())
    intent = ''
    sentiment = ''
    notif = 'no'
    dt = ''

    reminders = []
    if 'reminders' in per.keys():
        reminders = per['reminders']
        
    if bot_response['intents']:
        intent = bot_response['intents'][0]['name']

    if bot_response['traits'] and bot_response['traits']['wit$sentiment']:
        sentiment = bot_response['traits']['wit$sentiment'][0]['value']

    chat_response = 'Hmm..'

    if intent == 'get_name':
        #todo db call
        name = per['patient_name']
        chat_response = 'Haha your name is '+name+'\n Hello '+name+'!'
    
    elif intent == 'get_contact':
        #todo db call
        contact = per['emergency_pno']
        chat_response = 'Your emergency contact is '+contact+' take care.'

    elif intent == 'get_medicines':
        #todo db call
        
        medicines = per['medicines']
        
        chat_response = ''
        for i in medicines:
            medicine = [i['name'],i['hour'],i['min']]
            chat_response+= medicine[0]+' at '+str(medicine[1])+':'+str(medicine[2])+'\n'
        if chat_response:
            chat_response = 'Your medicines listed for today are:\n' + chat_response
        else:
            'no medicines listed!'
    elif intent == 'get_address':
        #todo db call
        address = per['address']
        chat_response = 'You live at '+address

    elif intent == 'get_greeting':
        chat_response = 'Hello, hope your day is going alright!'  
        #and other such greetings likewise -> can be finalized later
    elif intent == 'get_reminder':
    	if entity["wit$datetime:datetime"] and entity["wit$reminder:reminder"]:
            obj =  entity["wit$datetime:datetime"][0]["value"]
            date = obj[:10]
            time = obj[11:16]
            reminder = entity["wit$reminder:reminder"][0]["body"]
            chat_response = "Reminder set : "+reminder+" at "+time+" on "+date
            notif='yes'
            dt = date+' '+time
            reminders.append(" "+reminder+" at "+time+" on "+date+",")
            db.child('users').child(number).update({"reminders": reminders})

    elif intent == 'set_reminder':
        if reminders == []:
            chat_response = 'you dont have any reminders scheduled.'
        else:
            str_reminder = '\n'.join([str(elem) for elem in reminders])
            chat_response = "Your reminders/schedule is:\n" + str_reminder
    elif intent == "identify_person":
        chat_response = 'hmm..let me check.Send me a picture of the person.'
    elif intent == "guide_me":
        chat_response = 'Open the maps'
    elif sentiment == 'negative':
        chat_response = 'Oh no :( Things are going to get better. Wanna talk to someone?'

    response = dict()
    response['bot_response'] = bot_response
    response['chat_response'] = chat_response
    
    return response



#comment below call for local setup
if __name__ == '__app__':
     app.run() 

#Uncomment this for local run
#app.run(host="0.0.0.0",port=5000)  
