import asyncio
import copy

class Data:
    tasks = {}
    users = {}
    lock = asyncio.Lock()

def emergency_save():
    from json import dump
    print("Emergency Save...")
    try:
        with open("tasks.json", "w") as file:
            dump(Data.tasks, file)
            print("Saving all tasks...")
        with open("users.json", "w") as file:
            dump(Data.users, file)
            print("Saving all users...")
    except Exception as error:
        print(error)

async def back_up(interval = 3600):
    from json import dump
    async with Data.lock:
        print("Back up is working...")
        try:
            with open("tasks.json", "w") as file:
                dump(Data.tasks, file)
                print("Saving all tasks...")
            with open("users.json", "w") as file:
                dump(Data.users, file)
                print("Saving all users...")
        except Exception as error:
            print(error)
        if interval == 0:
            return


async def recover():
    from json import load
    async with Data.lock:
        try:
            with open("tasks.json") as file:
                data: dict = load(file)
                print("Getting all tasks...")
                Data.tasks = data

        except Exception as error:
            print(error)
            Data.tasks = {}
        try:
            with open("users.json") as file:
                data: dict = load(file)
                print("Getting all users...")
                a = {}
                for domain, participants in data.items():
                    a[domain] = {}
                    for k, v in participants.items():
                        a[domain][int(k)] = v
                Data.users = a
                if Data.users == {}:
                    Data.users = Data.users = {"admins":{},"users":{}}
        except Exception as error:
            print(error)
            Data.users = {"admins":{},"users":{}}


async def save_all_tasks(data: dict) -> None:
    print("save_all_tasks, single op in lock")
    async with Data.lock:
        Data.tasks = data


async def get_all_tasks() -> dict:
    print("get_all_tasks, single op in lock")
    async with Data.lock:
        return copy.deepcopy(Data.tasks)


async def add_new_task(task_data : tuple):
    print("add_new_task, get, add a key-value pair, set")
    data = await get_all_tasks()
    data[task_data[0]] = task_data[1::]
    await save_all_tasks(data)

async def del_a_task(task_id : str):
    print("del_a_task, get, dict pop, set")
    data = await get_all_tasks()
    if task_id in data.keys():
        data.pop(task_id, None)
    await save_all_tasks(data)


async def get_all_users() -> dict:

    print("get_all_users, single op in lock")
    async with Data.lock:
        return copy.deepcopy(Data.users)


async def save_all_users(data: dict) -> None:
    print("save_all_users, single op in lock")
    async with Data.lock:
        Data.users = data


async def check_if_user_exists(user_id: int) -> str:
    print("check_if_user_exists, get, 2x2 logic branch")
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
    print("add_new_user, get, 2 logic branch, set")
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
    print("accept_user, get, 2x2 logic branch, set")
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
