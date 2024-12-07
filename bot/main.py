from system import launch_bot
import datetime
import requests
import json
from pyngrok import ngrok, conf
from pyngrok.exception import PyngrokNgrokError
import subprocess
import time
import atexit
import os


def start_ngrok(token):
        conf.get_default().auth_token = token
        ngrok_process = subprocess.Popen(["ngrok", "http", str(8000)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        atexit.register(ngrok_process.terminate)
        atexit.register(ngrok.kill)
        while True:
            time.sleep(5)
            try:
                response = requests.get("http://127.0.0.1:4040/api/tunnels")
                tunnels = response.json()
                print(tunnels)
                public_url = tunnels['tunnels'][0]['public_url']
                return public_url
            except Exception as e:
                ngrok_process.terminate()
                ngrok.kill()
                raise RuntimeError("Failed to get public url, is ngrok running")

def first_kex():
    greeting = "Hi, t"
    hour = datetime.datetime.now().hour
    if hour >=5 and hour < 10:
        greeting = "Good Morning, t"
    if hour >=10 and hour < 13:
        greeting = "Awesome day, isn't it? T"
    elif hour >=13 and hour <=17:
        greeting = "Good Afternoon, t"
    elif hour >17 and hour <21:
        greeting = "God Evening, t"
    elif hour > 21 or hour < 5:
        greeting = "What a lovely night! T"

    print(f"\n\n\n{greeting}his is Task Manager bot created for TTPU adminstration")
    name = input("What is you name, by the way? ").capitalize()

    message1 = f"""Nice to meet you {name}, This program is a telegram bot server
Do you have the token of a vacant telegram bot?"""
    message2 = """Copy and past it here
And make sure that you have read README"""
    message3 = """Now, type the phone number of admin, please dont forget country code. """
    message4 = "Now I am launching the bot, please go to your telegram and open bot chat"
    message5 = """If you don't have a token, you can get one in telegram bot
called BotFather by creating a new bot, and don't forget to add /start command.
If you are troubled consult an IT specialist"""
    message6 = "(Yes or No | yes or no | y or n | 1 or 0 | any number or 0) "
    message7 = """Now input the auhttoken provided by ngrok
If you dont have ot you can sign up in ngrok.com and get authtoken in ngrok.setup.com"""

    print(message1, message6, sep="\n")

    def get_token():
        token = input(" Your token: ").strip()
        url = f"https://api.telegram.org/bot{token}/getMe"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Checking the validity of the token...")
                data = response.json()
                if data["ok"]:
                    print("Token is valid")
                    return token
                else:
                    print("Your token is invalid, please check it and try again ")
                    return get_token()
            elif response.status_code == 404:
                print("Your token is invalid, please check it and try again ")
                return get_token()
                
        except requests.RequestException as error:
            print(f"The following error ocurred during operation: {error}")
            return get_token()
        
    def get_number():
        num = input(" Phone number: ").strip()
        num = num.removeprefix("+")
        if not num.isdigit():
            print("Your number contains non digit symbols, try again")
            return get_number()
        else:
            return num

    def get_authtoken():
        token = input(" Your authtoken you can find it in http://ngrok/setup.com: ").strip()
        try:
            public_url = start_ngrok(token)
            return token, public_url
        except:
            print("Token is invalid, try again")
            return get_authtoken()

    while True:
        answer = input(" Answer: ").lower().strip()
        meaning = None
        if answer in ["yes", "ye", "y", "yeah", "ha", "da"]:
            meaning = True
        if answer in ["no", "n", "nah", "not", "ne", "yo'q", "net", "nea"]:
            meaning = False 
        elif answer.isdigit():
            if int(answer) != 0:
                meaning = True
            elif int(answer) == 0:
                meaning = False
        if not meaning is None:
            if meaning:
                print(message2)
                token = get_token()
                print(message3)
                num = get_number()
                print(message7)
                authtoken, public_url = get_authtoken()
                print(message4)
                return token, num, authtoken, public_url
            else:
                print(message5)
        else:
            print(message6)

def write_json(data:dict):
    with open(os.path.join('..', 'config.json'), 'w') as file:
            json.dump(data, file)


def start():
    token, number, authtoken, public_url = None, None, None, None
    try:
        with open(os.path.join('..', 'config.json'), "r") as file:
            config = json.load(file)
            if not config:
                raise ValueError
    except:
        config = {"token":None,"number":None, "authtoken":None}
    print(config)
    token = config["token"]
    number = config["number"]
    authtoken = config["authtoken"]
    if token and  number and authtoken:
        public_url = start_ngrok(authtoken)
        config["public_url"] = public_url
        write_json(config)
        print("Launching bot using pre-set settings...")
        print(config)
        launch_bot(token, number, public_url)
        config.pop("public_url")
        write_json(config)
        return
    else:
        token, number, authtoken, public_url = first_kex()
        config = {}
        config["token"] = token
        config["number"] = number
        config["authtoken"] = authtoken
        config["public_url"] = public_url
        print(config)
        write_json(config)
    
    launch_bot(token, number, public_url)

start()
a = []