from django.shortcuts import render
from .models import Task
import json
import os

def load_tasks():
    root = os.path.join("..",  "bot", "data")
    try:    
        backup_files = (os.listdir(root))
    except Exception as error:
        print(error)
    tasks_files = []
    users_files = []
    if not backup_files: return
    for i in backup_files:
        if "tasks" in i:
            tasks_files.append(i)
        if "users" in i:
            users_files.append(i)
    tasks_files.sort()
    users_files.sort()
    print(tasks_files)
    users = None
    tasks = None
    while True:
        try:
            path = os.path.join(root, tasks_files[-1])
            print(path)
            print(tasks_files[-1])
            with open(path) as file:
                data: dict = json.load(file)
                print("Getting tasks...")
                if not data:
                    raise Exception
                tasks = data
                break
        except Exception as error:
            print(error)
            if len(tasks_files)>1:
                print("Fetching next backup...")
                tasks_files.pop()
            else:
                print("Unable to recover any task data, all data lost!")
                break
    while True:    
        try:
            path = os.path.join(root, users_files[-1])
            print(users_files[-1])
            with open(path) as file:
                data: dict = json.load(file)
                print("Getting users...")
                if not data:
                    raise Exception
                users = data["users"]
        except Exception as error:
            print(error)
            if len(users_files)>1:
                print("Fetching next backup...")
                users_files.pop()
            else:
                print("Unable to recover any user data, all data lost!")
                break
        return tasks, users
                
def refine():
    task_data, user_data = load_tasks()
    if not task_data:
        return
    a = []
    for k, v in task_data.items():
        name  = v[0].split("\n")[0]
        description = v[0].removeprefix(name)
        started = ".".join(map(str, v[2]))
        ends = '.'.join(map(str, v[1]))
        users = ''
        completed_users = 0
        all_users = 0
        for u in v[3]:
            if u in v[5]:
                users += (f"{user_data[str(u)][2]} C")
                users += '\n'
                completed_users+=1
            elif u in v[4]:
                users += (f"{user_data[str(u)][2]} A")
                users += '\n'
                all_users+=1
            else:
                users += (f"{user_data[str(u)][2]} N")
                users += '\n'
            all_users+=1
        number_of_files = len(v[6].values())
        completeness = completed_users/all_users
        print(completeness)
        b = {"id":k, "name":name, "description":description, "users":users, "started_on":started, "ends_on":ends, "number_of_files" : number_of_files, 'completeness': completeness}
        a.append(b)
    return a

# Create your views here.
def task_dashboard(request):
    tasks = refine()
    
    if not tasks:
        tasks = Task.objects.all()
    return render(request, 'tasks/dashboard.html', {'tasks':tasks})