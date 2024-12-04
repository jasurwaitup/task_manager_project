from system import launch_bot
import datetime
import requests
import json


def first_kex():
    greeting = "Hi"
    hour = datetime.datetime.now().hour
    if hour >=5 and hour < 10:
        greeting = "Good Morning"
    if hour >=10 and hour < 13:
        greeting = "Awesome day, isn't it?"
    elif hour >=13 and hour <=17:
        greeting = "Good Afternoon"
    elif hour >17 and hour <21:
        greeting = "God Evening"
    elif hour > 21 or hour < 5:
        greeting = "What a lovely night!"

    print(f"\n\n\n{greeting} this is Task Manager bot created for TTPU adminstration")
    name = input("What is you name, by the way? ").capitalize()

    message1 = f"""Nice to meet you {name}, This program is a telegram bot server
Do you have the token of a vacant telegram bot?"""
    message2 = """Copy and past it here
If you're unable to paste, try Ctrl+Shift+V instead of Ctrl+V
And make sure that your bot has /start command, otherwise write /start manually when you enter chat"""
    message3 = """Now, type the phone number of admin, one who creates and assigns tasks.
This number is like starting point of functionality. You can omit plus sign. 
You can always change admins in the bot.
You can cnahge main phone number in config.json only if necessary """
    message4 = "Now I am launching the bot,please go to your telegram and open bot chat"
    message5 = """If you don't have a token, you can get one in telegram bot
called BotFather by creating a new bot, and don't forget to add /start command.
If you are troubled coucil an IT specialist"""
    message6 = "(Yes or No, yes or no, y or n, 1 or 0, any number or 0) "

    print(message1, message6, sep="\n")

    def get_token():
        token = input("your token: ").strip()
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
        num = input("number: ").strip()
        num = num.removeprefix("+")
        if not num.isdigit():
            print("Your number contains non digit symbols, try again")
            return get_number()
        else:
            return num


    while True:
        answer = input("answer: ").lower().strip()
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
                print(message4)
                return token, num
            else:
                print(message5)
        else:
            print(message6)


def start():
    token, number = None, None
    with open("../config.json", "r") as file:
        try:
            config = json.load(file)
            if not config:
                raise ValueError
        except:
            config = {"token":None,"number":None}
        print(config)
        token = config["token"]
        number = config["number"]
        if token and  number:
            print("Launching bot using custom settings...")
            launch_bot(token, number)
    with open("../config.json", "w") as file:
        token, number = first_kex()
        config = {}
        config["token"] = token
        config["number"] = number
        print(config)
        json.dump(config, file)
    
    launch_bot(token, number)

start()