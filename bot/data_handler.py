import asyncio
import copy
import datetime
import os

class Data:
    tasks = {}
    users = {}
    app_data = {}
    lock = asyncio.Lock()


root = "data"

def emergency_save():
    from json import dump
    print("Emergency Save...")
    time_prefix = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    root = "data"
    try:
        path = os.path.join(root, f"{time_prefix}tasks.json")
        with open(path, "w") as file:
            dump(Data.tasks, file, indent=2, ensure_ascii=True)
            print("Saving all tasks...")
        path = os.path.join(root, f"{time_prefix}users.json")
        with open(path, "w") as file:
            dump(Data.users, file, indent=2, ensure_ascii=True)
            print("Saving all users...")
        path = os.path.join(root, f"{time_prefix}app_data.json")
        with open(path, "w") as file:
            dump(Data.app_data, file, indent=4, ensure_ascii=True)
            print("Saving app_data...")
    except Exception as error:
        print(error)


async def back_up(context):
    from json import dump
    time_prefix = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    
    async with Data.lock:
        print("Back up is working...")
        try:
            path = os.path.join(root, f"{time_prefix}tasks.json")
            with open(path, "w") as file:
                dump(Data.tasks, file, indent=2, ensure_ascii=True)
                print("Saving all tasks...")
            path = os.path.join(root, f"{time_prefix}users.json")
            with open(path, "w") as file:
                dump(Data.users, file, indent=2, ensure_ascii=True)
                print("Saving all users...")
            path = os.path.join(root, f"{time_prefix}app_data.json")
            with open(path, "w") as file:
                dump(Data.app_data, file, indent=4, ensure_ascii=True)
                print("Saving app_data...")
        except Exception as error:
            print(error)
    backup_files = (os.listdir(root))
    tasks_files = []
    users_files = []
    app_data_files = []
    for i in backup_files:
        if "tasks" in i:
            tasks_files.append(i)
        elif "users" in i:
            users_files.append(i)
        elif "app_data" in i:
            app_data_files.append(i)
    while len(tasks_files) > 10:
        os.remove(os.path.join(root, tasks_files.pop()))
    while len(users_files) > 10:
        os.remove(os.path.join(root, users_files.pop()))
    while len(app_data_files) > 10:
        os.remove(os.path.join(root, app_data_files.pop()))
    


async def recover():
    from json import load
    try:    
        backup_files = (os.listdir(root))
    except Exception as error:
        print(error)
        os.makedirs(root, exist_ok=True)
        backup_files = (os.listdir(root))
    tasks_files = []
    users_files = []
    app_data_files = []
    for i in backup_files:
        if "tasks" in i:
            tasks_files.append(i)
        elif "users" in i:
            users_files.append(i)
        elif "app_data" in i:
            app_data_files.append(i)

    async with Data.lock:
        unfinished = True
        while unfinished:
            try:
                path = os.path.join(root, tasks_files[-1])
                with open(path) as file:
                    data: dict = load(file)
                    print("Getting all tasks...")
                    if not data:
                        raise Exception
                    Data.tasks = data
                    unfinished = False

            except Exception as error:
                print(error)
                if len(tasks_files):
                    print("Fetching next backup...")
                    tasks_files.pop()
                else:
                    print("Unable to recover any task data, all data lost!")
                    Data.tasks = {}
                    unfinished = False
        unfinished = True
        while unfinished:
            try:
                path = os.path.join(root, users_files[-1])
                with open(path) as file:
                    data: dict = load(file)
                    print("Getting all users...")
                    if not data:
                        raise Exception
                    a = {}
                    for domain, participants in data.items():
                        a[domain] = {}
                        for k, v in participants.items():
                            a[domain][int(k)] = v
                    print(a)
                    Data.users = a
                    unfinished = False
            except Exception as error:
                print(error)
                if len(users_files)>1:
                    users_files.pop()
                    print("Fetching next backup...")
                else:
                    print("Unable to recover any user data, all data lost!")
                    Data.users = {"admins":{},"users":{}}
                    unfinished = False
        unfinished = True
        while unfinished:
            try:
                path = os.path.join(root, app_data_files[-1])
                with open(path) as file:
                    data: dict = load(file)
                    if not data:
                        raise Exception
                    print("Getting app_data...")
                    Data.app_data = data
                    unfinished = False
            except Exception as error:
                print(error)
                if len(app_data_files)>1:
                    print("Fetching next backup...")
                    app_data_files.pop()
                else:
                    try:
                        print("Recovering critical app data")
                        with open(os.path.join("black_day", "app_data.json")) as file:
                            data = load(file)
                            if not data:
                                raise Exception
                            Data.app_data = data
                            unfinished = False
                    except:
                        print("Unable to recover any app data, BOT IS OUT OF USE")
                        Data.app_data={}
                        unfinished = False
 

async def get_app_data():
    async with Data.lock:
        return copy.deepcopy(Data.app_data) 
    

async def set_app_data(data):
    async with Data.lock:
        Data.app_data = copy.deepcopy(data)


async def save_all_tasks(data: dict) -> None:
    print("save_all_tasks")
    async with Data.lock:
        Data.tasks = data


async def get_all_tasks() -> dict:
    print("get_all_tasks")
    async with Data.lock:
        return copy.deepcopy(Data.tasks)


async def add_new_task(task_data : tuple):
    print("add_new_task")
    data = await get_all_tasks()
    data[task_data[0]] = task_data[1::]
    await save_all_tasks(data)


async def del_a_task(task_id : str):
    print("del_a_task")
    data = await get_all_tasks()
    if task_id in data.keys():
        data.pop(task_id, None)
    await save_all_tasks(data)


async def get_all_users() -> dict:

    print("get_all_users")
    async with Data.lock:
        return copy.deepcopy(Data.users)


async def save_all_users(data: dict) -> None:
    print("save_all_users")
    async with Data.lock:
        Data.users = data


async def check_if_user_exists(user_id: int) -> str:
    print("check_if_user_exists")
    users_dict = await get_all_users()
    if user_id in users_dict["users"].keys():
        if users_dict["users"][user_id][-1]:
            return "+user"
        elif not users_dict["users"][user_id][-1]:
            return "-user"
    elif user_id in users_dict["admins"].keys():
        if users_dict["admins"][user_id][-1]:
            return "+admin"
        elif not users_dict["admins"][user_id][-1]:
            return "-admin"
    else:
        return "guest"


async def add_new_user(username, phone_number, user_id, fullname, is_activated=False, is_admin=False) -> None:
    print("add_new_user")
    """{"users": {"user_id": ["phone_number1", "username", "fullname", is_activated],
                   "other user": []},
         "admins": {"user_id": ["phone_number2", "username", "fullname", is_activated],
                    "other admin": []}
         }"""
    data = await get_all_users()
    if is_admin:
        data["admins"][user_id] = [phone_number, username, fullname, is_activated]
    elif not is_admin:
        data["users"][user_id] = [phone_number, username, fullname, is_activated]
    print("A new user is added")
    await save_all_users(data)


async def accept_user(user_id, is_accepted, is_admin):
    # JSON don't allow dict keys to be integers
    # It converts them into strings
    print("accept_user")
    data = await get_all_users()
    if not is_admin:
        if user_id in data["users"].keys():
            if is_accepted:
                data["users"][user_id][-1] = True
                print("Accepted user")
            elif not is_accepted:
                print("Declined user")
                data["users"].pop(user_id)
    elif is_admin:
        if user_id in data["admins"].keys():
            if is_accepted:
                print("Accepted admin")
                data["admins"][user_id][-1] = True
            elif not is_accepted:
                print("Declined admin")
                data["admins"].pop(user_id)
    await save_all_users(data)
