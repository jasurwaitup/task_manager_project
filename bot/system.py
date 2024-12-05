import data_handler
from classes import User, Admin, Task, Participant



import re
import signal
import sys





from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove


TOKEN = "7910267092:AAHaytMo5F4KI8Zt3luCt9wIR3Uz6Jr037E"


IS_EDITING_DESCRIPTION = 5
IS_EDITING_YEAR = 6
IS_EDITING_MONTH = 7
IS_EDITING_DAY = 8
IS_EDITING_ATTACHED_USERS = 9
IS_ATTACHING_FILES = 10
IS_EDITING_TASK = 11
IS_COMMENTING = 12
IS_CHANGING_PREFERENCES = 13

IS_GUEST = 0
IS_GIVING_NUMBER = 1
IS_TYPING_PASSWORD = 2
IS_WAITING_FOR_ACCEPTATION = 3
IS_REGISTERED = 4
STATE = 0

STATES = {}



State_names_for_convenience = ["IS_GUEST", "IS_GIVING_NUMBER", "IS_TYPING_PASSWORD",
                               "IS_WAITING_FOR_ACCEPTATION", "IS_REGISTERED", "IS_EDITING_DESCRIPTION", "IS_EDITING_YEAR","IS_EDITING_MONTH",
                                "IS_EDITING_DAY", "IS_EDITING_ATTACHED_USERS", "IS_ATTACHING_FILES", "IS_EDITING_TASK",
                               "IS_COMMENTING"]





async def show_task_list(update : Update,context : ContextTypes.DEFAULT_TYPE , to_admin : bool , all_tasks : bool = False):
    print("show_task_list")
    user_id = update.effective_user.id
    tasks = await data_handler.get_all_tasks()
    all_users =await data_handler.get_all_users()
    if context.user_data["cache"]:
        await clean(context, None, user_id)

    header = "All the tasks"
    if not tasks: header = "No tasks yet"
    x = await update.effective_message.reply_text(header)
    context.user_data["cache"] = {}
    context.user_data["cache"]["0"] = [x.message_id]


    for key, values in tasks.items():
        is_user_attached = user_id in values[3]
        if not to_admin and not all_tasks:
            if user_id in values[5] or not is_user_attached:
                continue
        task_data = (key, *values)
        a_task = Task(*task_data)
        body, markup = await a_task.show_me(to_admin, user_id, all_users=all_users)
        
        x = await update.effective_message.reply_text(body, reply_markup=[None,markup][is_user_attached or to_admin])
        context.user_data["cache"][key] = [x.message_id]

        comments_header = "Comments:\n\n"
        comments_body = ""
        comments_dict = a_task.get_comments()
        for author, his_comments in comments_dict.items():
            if his_comments:
                author = int(author)
                if author in all_users["admins"]:
                    author_name = all_users["admins"][author][2]
                else:
                    author_name = all_users["users"][author][2]
                comments_body += f"{author_name}:\n"
                for comment in his_comments:
                    comments_body += f"* {comment}\n"
            comments_body += "\n\n"
        if comments_body:
            x = await update.effective_message.reply_text(comments_header+comments_body)
            context.user_data["cache"][key].append(x.message_id)

        files = a_task.get_files()
        if files:
            for owner in files.keys():
                for a_file in files[owner]:
                    name = ""
                    if user_id in all_users["admins"]:
                        name = "Admin"
                    else:
                        name = all_users["users"][int(owner)][2]
                    file =  await update.get_bot().get_file(a_file)
                    if file.file_path.split(".")[-1] in ["jpg", "png", "webp"]:
                        x = await update.effective_message.reply_photo(caption=name, photo=a_file)
                    else:
                        x = await update.effective_message.reply_document(caption=name, document=a_file)
                    context.user_data["cache"][key].append(x.message_id)


async def clean(context:ContextTypes.DEFAULT_TYPE, message_id, user_id, inverse : bool = False):
    x = {}
    print("clean")
    for task_id, message_ids in context.user_data["cache"].items():
        if inverse:
            if task_id == message_id:
                for a_message_id in message_ids:
                    await context.bot.delete_message(user_id, a_message_id)
                    continue
            x[task_id] = message_ids
        else:
            for a_message_id in message_ids:
                if message_id == a_message_id:
                    x[task_id] = [message_id]
                    continue
                await context.bot.delete_message(user_id, a_message_id)
    if message_id:
        context.user_data["cache"] = x
        return
    context.user_data["cache"] = {}


async def identify_participant(user_id, context : ContextTypes.DEFAULT_TYPE):
    global STATES
    #We must check every time when user or admin (participant in general)
    #intercats with bot to be sure who we are dealing with.
    user_type = await data_handler.check_if_user_exists(user_id)
    if not "cache" in context.user_data.keys():
        context.user_data["cache"] = {}
    if not "flag" in context.user_data.keys():
        context.user_data["flag"] = None
    if user_id not in STATES.keys():
        STATES[user_id] = IS_GUEST

    if STATES[user_id] in [0, 1, 2, 3] and "+" in user_type:
        STATES[user_id] = IS_REGISTERED

    return user_type


async def handle_keyboard_buttons(update : Update, context : ContextTypes.DEFAULT_TYPE):
    global STATES

    user_id = update.effective_user.id
    user_type = await identify_participant(user_id, context)
    message = update.message.text

    print(State_names_for_convenience[STATES[user_id]], f"for {update.effective_user.full_name}")
    if "+admin" == user_type:
        if message == "Cancel":
            await update.effective_message.delete()
            if STATES[user_id] in list(range(4,12)):
                STATES[user_id] = IS_REGISTERED
                await update.message.reply_text("Canceled", reply_markup=Admin.ADMIN_MENU)
                await clean(context, None, user_id)
                context.user_data["current_task"] = None
                context.user_data["flag"] = None
                return
        if STATES[user_id] == IS_REGISTERED:
            if message == "New Task" :
                await update.effective_message.delete()
                STATES[user_id] = IS_EDITING_DESCRIPTION
                context.user_data["current_task"] = Task()
                x = await update.message.reply_text("Input description: ", reply_markup=Admin.CANCEL_MENU)
                context.user_data["last_markup_message"] = x.message_id
                return
            elif message == "Task List":
                await update.effective_message.delete()
                await show_task_list(update, context,True )
        elif STATES[user_id] == IS_EDITING_DESCRIPTION:
            if message != "New Task":
                context.user_data["current_task"].set_description(message)
                STATES[user_id] = IS_EDITING_TASK
                if not type(context.user_data["flag"]) == str:
                    year_menu = await Admin.edit_deadline(step=0)
                    x = await update.message.reply_text("Choose deadline year", reply_markup=year_menu)
                    context.user_data["last_markup_message"] = x.message_id
                    STATES[user_id] = IS_EDITING_YEAR
                    return
        elif STATES[user_id] == IS_EDITING_YEAR:
            context.user_data["current_task"].set_deadline(2,message)
            month_key = await Admin.edit_deadline(step = 1,year =  int(message))
            x = await update.message.reply_text("Choose deadline month", reply_markup=month_key)
            context.user_data["last_markup_message"] = x.message_id
            STATES[user_id] = IS_EDITING_MONTH
            return
        elif STATES[user_id] == IS_EDITING_MONTH:
            month_names = ["Jan", "Feb", "March", "Apr", "May", "June", "July", "Aug", "Sept", "Oct", "Nov", "Dec"]
            context.user_data["current_task"].set_deadline(1, month_names.index(message)+1)
            day_key = await Admin.edit_deadline(step = 2, year=context.user_data["current_task"].get_deadline()[2], month =message)
            x = await update.message.reply_text("Choose day", reply_markup=day_key)
            context.user_data["last_markup_message"] = x.message_id
            STATES[user_id] = IS_EDITING_DAY
            return
        elif STATES[user_id] == IS_EDITING_DAY:
            context.user_data["current_task"].set_deadline(0, int(message))
            STATES[user_id] = IS_EDITING_TASK
            if not type(context.user_data["flag"]) == str:
                user_key = await Admin.edit_users(context.user_data["current_task"])
                await update.message.reply_text(f"Deadline is set to {context.user_data["current_task"].get_deadline()}", reply_markup=Participant.CANCEL_MENU)
                x = await update.message.reply_text("Attach users", reply_markup=user_key)
                context.user_data["last_markup_message"] = x.message_id
                STATES[user_id] = IS_EDITING_ATTACHED_USERS
                return
        elif STATES[user_id] == IS_EDITING_ATTACHED_USERS:
            pass
        elif STATES[user_id] == IS_EDITING_TASK:
            await update.effective_message.delete()
    elif "+user" == user_type:
        if message == "Cancel":
            await update.message.reply_text("Canceled", reply_markup=User.USER_MENU)
            STATES[user_id] = IS_REGISTERED
            return
        if STATES[user_id] == IS_REGISTERED:
            if message == "Task List":
                await show_task_list(update, context, False, all_tasks=True )
            if message == "My Tasks":
                await show_task_list(update, context, False, all_tasks=False)
    if STATES[user_id] == IS_GUEST:
        if message == "User":
            context.user_data["flag"] = False
            STATES[user_id] = IS_GIVING_NUMBER
            await show_registration_menu(update, context, menu_type="contact")
        if message == "Admin":
            context.user_data["flag"] = True
            STATES[user_id] = IS_GIVING_NUMBER
            await show_registration_menu(update, context, menu_type="contact")
        return
    elif STATES[user_id] == IS_GIVING_NUMBER:
        if update.effective_message.contact.phone_number.removeprefix("+") in Admin.Super_Admin_Numbers:
            x = await update.message.reply_text("You are accepted as super admin!", reply_markup=Admin.ADMIN_MENU)
            context.user_data["last_markup_message"] = x.message_id
            STATES[user_id] = IS_REGISTERED
            await data_handler.add_new_user(update.effective_user.username,
                                           update.effective_message.contact.phone_number,
                                           update.effective_user.id, update.effective_user.full_name,
                                           True, True)
            return
        else:

            await data_handler.add_new_user(update.effective_user.username, update.effective_message.contact.phone_number,
                                      update.effective_user.id, update.effective_user.full_name,
                                       False,  context.user_data["flag"])
        if not context.user_data["flag"]:
            await show_registration_menu(update, context, menu_type="applied")
            STATES[user_id] = IS_WAITING_FOR_ACCEPTATION
        elif context.user_data["flag"]:
            await show_registration_menu(update, context, menu_type="password")
            STATES[user_id] = IS_TYPING_PASSWORD
        context.user_data["flag"] = None
        return
    elif STATES[user_id] == IS_TYPING_PASSWORD:
        if "admin" not in user_type:
            print("This admin is object of User")
        if message == Admin.Admin_Password:
            await show_registration_menu(update, context, menu_type="Your application will be reviewed")
            STATES[user_id] = IS_WAITING_FOR_ACCEPTATION
        return
    elif STATES[user_id] == IS_ATTACHING_FILES:
        if message == "Ok":
            if not context.user_data["flag"]:
                STATES[user_id] = IS_REGISTERED
                x = await update.message.reply_text("Files are ready", reply_markup=[User.USER_MENU, Admin.ADMIN_MENU]["admin" in user_type])
                context.user_data["last_markup_message"] = x.message_id
                await data_handler.add_new_task(context.user_data["current_task"].to_tuple())
            if context.user_data["flag"]:
                STATES[user_id] = IS_REGISTERED
                x = await update.message.reply_text("File(s) attached",
                                                reply_markup=[User.USER_MENU, Admin.ADMIN_MENU]["admin" in user_type])
                context.user_data["last_markup_message"] = x.message_id
                await data_handler.add_new_task(context.user_data["current_task"].to_tuple())
    elif STATES[user_id] == IS_COMMENTING:
        context.user_data["current_task"].add_comment(user_id, message)
        await data_handler.add_new_task(context.user_data["current_task"].to_tuple())
        STATES[user_id] = IS_REGISTERED
        x = await update.effective_message.reply_text("Commented", reply_markup=[User.USER_MENU, Admin.ADMIN_MENU]["admin" in user_type])
        context.user_data["last_markup_message"] = x.message_id


async def handle_inline_buttons(update: Update, context : ContextTypes.DEFAULT_TYPE):
    data = update.callback_query
    await data.answer()
    user_id = update.effective_user.id
    user_type = await identify_participant(user_id, context)

    print(f"Inline {data.data} hit")

    pattern = r'^[a-zA-Z]\d+$'

    if user_type == "+admin":
        #USER OR ADMIN ACCEPTATION
        if  data.data[0] in ["+", "-", "*", "/"]:
            if "+" in data.data:
                await Admin.handle_ok_button(update, context, data.data)
            elif "-" in data.data:
                await Admin.handle_no_button(update, context, data.data)
            elif "*" in data.data:
                a = data.data.removeprefix("*")
                await data_handler.del_a_task(a)
                await update.effective_message.delete()
                await update.effective_message.reply_text("Deleted")
                print(context.user_data["cache"])
                if a in context.user_data["cache"].keys():
                    await clean(context, a, user_id, True)
            elif "/" in data.data:
                await update.effective_message.delete()
                await update.effective_message.reply_text("Left, You can delete it in edit menu")
        if STATES[user_id] == IS_EDITING_ATTACHED_USERS:
            if data.data == "OK":
                    #ATTACHED USERS EDITING
                if type(context.user_data["flag"]) == str:
                    await update.effective_message.edit_reply_markup(Admin.EDIT_MENU)
                    STATES[user_id] = IS_EDITING_TASK

                    #NOT EDITING, CREATING A NEW TASK
                elif type(context.user_data["flag"]) != str:
                    STATES[user_id] = IS_ATTACHING_FILES
                    x = await update.effective_message.reply_text("Now attach files, if you have none just hit Ok", reply_markup=Participant.ATTACH_FILE_MENU)
                    context.user_data["last_markup_message"] = x.message_id
            else:
                #ADMIN IS RADIO BUTTONING USERS
                user_list = await Admin.edit_users(context.user_data["current_task"], int(data.data))
                await update.effective_message.edit_reply_markup(user_list)
        if STATES[user_id] == IS_EDITING_TASK:
            if "des" == data.data:
                STATES[user_id] = IS_EDITING_DESCRIPTION
                x = await update.effective_message.reply_text("Input description: ", reply_markup=Admin.CANCEL_MENU)
                context.user_data["last_markup_message"] = x.message_id
                return
            elif "dea" == data.data:
                year_menu = await Admin.edit_deadline(step=0)
                x = await update.effective_message.reply_text("Choose deadline year", reply_markup=year_menu)
                context.user_data["last_markup_message"] = x.message_id
                STATES[user_id] = IS_EDITING_YEAR
                return
            elif "use" == data.data:
                user_key = await Admin.edit_users(context.user_data["current_task"])
                await update.effective_message.edit_reply_markup(user_key)
                STATES[user_id] = IS_EDITING_ATTACHED_USERS
                return
            elif "del" == data.data:
                await update.effective_message.edit_reply_markup(reply_markup=Participant.INLINE_DIALOG)
            elif "don" == data.data:
                await data_handler.add_new_task(context.user_data["current_task"].to_tuple())
                await clean(context, None, user_id)
                context.user_data["flag"] = None
                STATES[user_id] = IS_REGISTERED
                await update.effective_message.reply_text("Edited", reply_markup=Admin.ADMIN_MENU)
            elif "can" == data.data:
                await clean(context, None, user_id)
                context.user_data["flag"] = None
    if user_type == "+user":
        pass
    if re.match(pattern, data.data):
        # EDITING
        all_tasks = await data_handler.get_all_tasks()
        task = (data.data[1::], *all_tasks[data.data[1::]])
        context.user_data["current_task"] = Task(*task)
        context.user_data["lastly_notified"] = {}
        context.user_data["lastly_notified"][context.user_data["current_task"].get_id()] = False
        if "e" in data.data and user_type == "+admin":
            STATES[user_id] = IS_EDITING_TASK
            context.user_data["flag"] = data.data.removeprefix("e")
            x = await update.effective_message.edit_reply_markup(reply_markup=Admin.EDIT_MENU)
            await clean(context, x.message_id, user_id)
        elif "n" in data.data and user_type == "+admin":
            if not context.user_data["lastly_notified"][context.user_data["current_task"].get_id()]:
                await notify_users(context, context.user_data["current_task"].get_attached_users(), "reminder",
                                   data=f"It ends on {context.user_data["current_task"].get_deadline(True)}")
                a = await context.user_data["current_task"].show_me(True, user_id, True)[1]
                await update.effective_message.edit_reply_markup(reply_markup=a)
                context.user_data["lastly_notified"] = True
        elif "c" in data.data and context.user_data["cache"]:
            await clean(context, None, user_id)
            await update.effective_message.reply_text("Write your comment")
            STATES[user_id] = IS_COMMENTING
        elif "f" in data.data and context.user_data["cache"]:
            await clean(context, None, user_id)
            x = await update.effective_message.reply_text("Attach your file", reply_markup=Participant.ATTACH_FILE_MENU)
            context.user_data["last_markup_message"] = x.message_id
            STATES[user_id] = IS_ATTACHING_FILES
        elif "a" in data.data :
            context.user_data["flag"] = "acc"
            await update.effective_message.edit_reply_markup(Participant.INLINE_DIALOG)
        elif "z" in data.data :
            if user_id in context.user_data["current_task"].get_accepted_users():
                context.user_data["flag"] = "com"
                await update.effective_message.edit_reply_markup(Participant.INLINE_DIALOG)
            else:
                await update.effective_message.edit_reply_markup(await context.user_data["current_task"].show_me(user_id=user_id, for_markup_edit=True, light_accept=True))
    elif data.data == "yes":
        #for deleting task
        if context.user_data["flag"].isdigit():
            await data_handler.del_a_task(context.user_data["flag"])
            await clean(context, None, user_id)
            await update.effective_message.reply_text("Deleted")
            context.user_data["flag"] = None
            context.user_data["current_task"] = None
            #for accepting task
        elif context.user_data["flag"] in ["acc", "com"]:
            if context.user_data["flag"] == "acc":
                context.user_data["current_task"].add_accepted_user(user_id)
            else:
                context.user_data["current_task"].add_completed_user(user_id)
                if set(context.user_data["current_task"].get_completed_users()) == set(context.user_data["current_task"].get_attached_users()):
                    await notify_admins(context, user_id, "task_is_done", args=[context.user_data["current_task"].get_id()])
            await data_handler.add_new_task(context.user_data["current_task"].to_tuple())
            markup =await  context.user_data["current_task"].show_me(False, user_id, False)[1]
            await update.effective_message.edit_reply_markup(markup)
            context.user_data["current_task"] = None
            context.user_data["flag"] = None
    elif data.data == "no":
        # for deleting task
        if context.user_data["flag"].isdigit():
            await update.effective_message.edit_reply_markup(reply_markup=Admin.EDIT_MENU)
        elif context.user_data["flag"] in ["acc", "com"]:
            await update.effective_message.edit_reply_markup(reply_markup=await context.user_data["current_task"].show_me()[1])
            context.user_data["current_task"] = None
            context.user_data["flag"] = None


async def handle_file_inputs(update: Update, context : ContextTypes.DEFAULT_TYPE):
    global STATES
    user_id = update.effective_user.id
    await identify_participant(user_id, context)
    if STATES[user_id] == IS_ATTACHING_FILES:
        doc = update.effective_message.document
        img = update.effective_message.photo
        if doc:
            context.user_data["current_task"].add_file(user_id, doc.file_id)
        elif img:
            img = img[-1]
            context.user_data["current_task"].add_file(user_id, img.file_id)


async def handle_messages(update : Update, context : ContextTypes.DEFAULT_TYPE):
    pass


async def show_registration_menu(update : Update, context: ContextTypes.DEFAULT_TYPE, menu_type : str, user_id : int = None):
    #It suggests a registration interface
    #There are only 2 interfaces:
    # 1) Registration
    # 2) Main
    if not user_id:
        user_id = update.effective_user.id
    keyboard = None
    message = None
    if menu_type == "type":
        message = "Doing tasks or Making tasks"
        keyboard = [[KeyboardButton("User"), KeyboardButton("Admin")]]
    elif menu_type == "contact":
        message = "Please, share your phone number"
        keyboard = [[KeyboardButton("Share Phone Number", request_contact=True)]]
    elif menu_type == "password":
        message = "Please, type admin password provided by the rector"
        pass
    elif menu_type == "applied":
        message = "Your request will be reviewed"
        keyboard = None
        await notify_admins( context, update.effective_user.id ,"acceptance")
    elif menu_type == "waiting":
        message = "Your request is being reviewed"
        keyboard = None
    if keyboard:
        markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    else:
        markup = ReplyKeyboardRemove()
    x = await context.bot.sendMessage(user_id, message, reply_markup=markup)
    context.user_data["last_markup_message"] = x.message_id


async def notify_users(context : ContextTypes.DEFAULT_TYPE, users_list, not_type, data=None):
    #This function is responsible for sending different messages 
    #and notifications to users
    if not_type == "reminder":
        for i in users_list:
            await context.bot.sendMessage(i, f"Hey you got task! \n{data}")


async def notify_admins(context : ContextTypes.DEFAULT_TYPE, user_id : int ,type_ : str, args : list = None):
    #This function is responsible for sending different messages 
    #and notifications to admins
    all_users =await  data_handler.get_all_users()
    message = ""
    yes_key = None
    no_key = None
    if type_ == "acceptance":
        if user_id in all_users["users"]:
            is_admin = ""
            name = all_users["users"][user_id][2]
        elif user_id in all_users["admins"]:
            is_admin = "as an admin"
            name = all_users["admins"][user_id][2]
        else:
            print("Cant accept cuz user is not found in json")
            return
        message = f"A user {name} wants to join the team. {is_admin}"
        yes_key = InlineKeyboardButton("OK", callback_data=f"+{user_id}")
        no_key = InlineKeyboardButton("NO", callback_data=str(-user_id))
    elif type_ == "task_is_done":
        message = "Task is complete, delete the task?"
        yes_key = InlineKeyboardButton("OK", callback_data=f"*{args[0]}")
        no_key = InlineKeyboardButton("NO", callback_data=f"/{args[0]}")
    for admin_id, data in all_users["admins"].items():
        if yes_key and no_key:
            markup = InlineKeyboardMarkup([[yes_key, no_key]])
            await context.bot.sendMessage(admin_id, message,reply_markup=markup)


async def handle_commands(update : Update, context : ContextTypes.DEFAULT_TYPE):
    #All commands are operated here
    global STATES
    user_id = update.effective_user.id
    await identify_participant(user_id, context)
    user_type = await data_handler.check_if_user_exists(user_id)
    command = update.message.text[1:]



    if command == "start":
        if user_type == "+admin":
            x = await update.message.reply_text("Welcome back", reply_markup=Admin.ADMIN_MENU)
            context.user_data["last_markup_message"] = x.message_id
            STATES[user_id] = IS_REGISTERED
        elif user_type == "-admin":
            await update.message.reply_text("Wait bitch")
        elif user_type == "+user":
            x = await update.message.reply_text("Welcome back", reply_markup=User.USER_MENU)
            context.user_data["last_markup_message"] = x.message_id
            STATES[user_id] = IS_REGISTERED
        elif user_type == "-user":
            await update.message.reply_text("Wait")
        else:
            STATES[user_id] = IS_GUEST
            await  update.message.reply_text("Hello")
            await show_registration_menu(update, context, "type")


def graceful_shutdown(signum, frame):
    print("Shutting Down...")
    data_handler.emergency_save()
    sys.exit()

async def post_polling(app : Application):
    print("Setting schedule...")
    await data_handler.recover()
    app.job_queue.run_repeating(data_handler.back_up, interval=600)



def launch_bot(token=TOKEN, admin_number:str=None):
    #Very first, core function that initiates bot.
    #This function is called only once in the whole bot's lifetime

    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    app = Application.builder()
    app.token(token)

    app.read_timeout(30)
    app.write_timeout(30)
    app.post_init(post_polling)
    app = app.build()

    if admin_number:
        Admin.Super_Admin_Numbers.append(admin_number)

    app.add_handler(CallbackQueryHandler(handle_inline_buttons))
    app.add_handler(CommandHandler("start", handle_commands))
    app.add_handler(MessageHandler(filters.CONTACT, handle_keyboard_buttons))
    app.add_handler(MessageHandler(filters.TEXT, handle_keyboard_buttons))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file_inputs))
    app.add_handler(MessageHandler(filters.PHOTO, handle_file_inputs))
    print("Bot is starting...")
    app.run_polling()


if __name__ == '__main__':
    launch_bot()
