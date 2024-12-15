import asyncio.log
import data_handler
from classes import User, Admin, Task, Participant
from functionality import Markup

import re
import atexit
import sys
import asyncio
import copy

from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, \
    ReplyKeyboardRemove

TOKEN = "7910267092:AAHaytMo5F4KI8Zt3luCt9wIR3Uz6Jr037E"
APP_DATA = {}
DASHBOARD_URL = ""
BACKUP_INTERVAL = 600
READ_TIMEOUT = 30
WRITE_TIMEOUT = 30
FIRST_BACKUP = 60

IS_EDITING_DESCRIPTION = 5
IS_EDITING_YEAR = 6
IS_EDITING_MONTH = 7
IS_EDITING_DAY = 8
IS_EDITING_ATTACHED_USERS = 9
IS_ATTACHING_FILES = 10
IS_EDITING_TASK = 11
IS_COMMENTING = 12
IS_CHANGING_PREFERENCES = 13
IS_CHANGING_REMINDER_INTERVAL = 14
IS_CHANGING_ADMIN_PASSWORD = 15
IS_CHANGING_textual_content = 16

IS_GUEST = 0
IS_GIVING_NUMBER = 1
IS_TYPING_PASSWORD = 2
IS_WAITING_FOR_ACCEPTATION = 3
IS_REGISTERED = 4




State_names_for_convenience = ["IS_GUEST", "IS_GIVING_NUMBER", "IS_TYPING_PASSWORD",
                               "IS_WAITING_FOR_ACCEPTATION", "IS_REGISTERED", "IS_EDITING_DESCRIPTION",
                               "IS_EDITING_YEAR", "IS_EDITING_MONTH",
                               "IS_EDITING_DAY", "IS_EDITING_ATTACHED_USERS", "IS_ATTACHING_FILES", "IS_EDITING_TASK",
                               "IS_COMMENTING", "IS_CHANGING_PREFERENCES", "IS_CHANGING_REMINDER_INTERVAL", "IS_CHANGING_ADMIN_PASSWORD",
                               "IS_CHANGING_textual_content"]


async def get_from_app_data(keys:list=[]):
    print("get_from_app_data")
    lock= asyncio.Lock()
    data = {}
    async with lock:
        for k in keys:
            data[k] = copy.deepcopy(APP_DATA.get(k, None))
    return data



async def set_app_data(data:dict={}):
    lock= asyncio.Lock()
    async with lock:
        for k, v in data.items():
            APP_DATA[k] = v


async def show_task_list(update: Update, context: ContextTypes.DEFAULT_TYPE, to_admin: bool, all_tasks: bool = False):
    print("show_task_list")
    user_id = update.effective_user.id
    tasks = await data_handler.get_all_tasks()
    all_users = await data_handler.get_all_users()
    app_data = await get_from_app_data(["textual_content", "button_texts"])
    #if context.user_data["cache"]:
        #await clean(context, None, user_id)

    header = Markup.all_tasks
    if not tasks: header = Markup.no_tasks
    x = await update.effective_message.reply_text(header)
    context.user_data["cache"] = []
    #context.user_data["cache"]["0"] = [x.message_id]
    context.user_data["cache"].append(x.message_id)

    for key, values in tasks.items():
        is_user_attached = user_id in values[3]
        if not to_admin and not all_tasks:
            if user_id in values[5] or not is_user_attached:
                continue
        task_data = (key, *values)
        a_task = Task(*task_data)
        body, markup = await a_task.show_me(app_data, is_for_admin=to_admin, user_id=user_id, all_users=all_users)

        x = await update.effective_message.reply_text(body, reply_markup=[None, markup][is_user_attached or to_admin])
        #context.user_data["cache"][key] = [x.message_id]
        context.user_data["cache"].append(x.message_id)

        comments_header = f"{app_data["textual_content"]["comments_header"][0]}:\n\n"
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
            x = await update.effective_message.reply_text(comments_header + comments_body)
            #context.user_data["cache"][key].append(x.message_id)
            context.user_data["cache"].append(x.message_id)

        files = a_task.get_files()
        if files:
            for owner in files.keys():
                for a_file in files[owner]:
                    name = ""
                    if int(owner) in all_users["admins"]:
                        name = "Admin"
                    else:
                        name = all_users["users"][int(owner)][2]
                    file = await update.get_bot().get_file(a_file)
                    if file.file_path.split(".")[-1] in ["jpg", "png", "webp"]:
                        x = await update.effective_message.reply_photo(caption=name, photo=a_file)
                    else:
                        x = await update.effective_message.reply_document(caption=name, document=a_file)
                    #context.user_data["cache"][key].append(x.message_id)
                    context.user_data["cache"].append(x.message_id)


async def clean(context: ContextTypes.DEFAULT_TYPE, message_id, user_id, inverse: bool = False):
    x = []
    print("clean")
    for m_i in context.user_data["cache"]:
        if inverse:
            if m_i == message_id:
                await context.bot.delete_message(user_id, m_i)
                continue
            x.append(m_i)
        else:
            if message_id == m_i:
                x.append(m_i)
                continue
            await context.bot.delete_message(user_id, m_i)
    if message_id:
        context.user_data["cache"] = x
        return
    context.user_data["cache"] = []


async def identify_participant(user_id, context: ContextTypes.DEFAULT_TYPE):
    # We must check every time when user or admin (participant in general)
    # intercats with bot to be sure who we are dealing with.
    user_type = await data_handler.check_if_user_exists(user_id)
    if not "cache" in context.user_data.keys():
        context.user_data["cache"] = {}
    if not "flag" in context.user_data.keys():
        context.user_data["flag"] = None
    if not "state" in context.user_data.keys():
        context.user_data["state"] = IS_GUEST
    if not "current_task" in context.user_data.keys():
         context.user_data["current_task"] = None
    if context.user_data["state"] in [0, 1, 2, 3] and "+" in user_type:
        context.user_data["state"] = IS_REGISTERED
    print("flag, cache, current_task", context.user_data["flag"], context.user_data["cache"], context.user_data["current_task"])
    return user_type


async def handle_keyboard_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    user_type = await identify_participant(user_id, context)
    app_data =await  get_from_app_data(["textual_content", "button_texts"])
    message = update.message.text

    print(State_names_for_convenience[context.user_data["state"]], f"for {update.effective_user.full_name}")
    if "+admin" == user_type:
        if message == Markup.cancel:
            await update.effective_message.delete()
            if context.user_data["state"] in list(range(4, 17)):
                context.user_data["state"] = IS_REGISTERED
                await update.message.reply_text(Markup.canceled, reply_markup=Admin.ADMIN_MENU)
                context.user_data["current_task"] = None
                context.user_data["flag"] = None
                return
        if context.user_data["state"] == IS_REGISTERED:
            if message == Markup.new_task:
                context.user_data["state"] = IS_EDITING_DESCRIPTION
                context.user_data["current_task"] = Task()
                await update.message.reply_text(Markup.input_description, reply_markup=Admin.CANCEL_MENU)
                return
            elif message == Markup.task_list:
                await show_task_list(update, context, True)
            elif message ==Markup.pref:
                context.user_data["state"] = IS_CHANGING_PREFERENCES
                await update.effective_message.reply_text(Markup.what_change, reply_markup=Admin.PREFERENCES_MENU)
            elif message == Markup.dashboard:
                await update.effective_message.reply_text(DASHBOARD_URL)
        elif context.user_data["state"] == IS_EDITING_DESCRIPTION:
            if message != Markup.new_task:
                context.user_data["current_task"].set_description(message)
                await update.effective_message.reply_text("Set")
                context.user_data["state"] = IS_EDITING_TASK
                if not type(context.user_data["flag"]) == str:
                    year_menu = await Admin.edit_deadline(step=0)
                    x = await update.message.reply_text(Markup.choose_year, reply_markup=year_menu)
                    context.user_data["state"] = IS_EDITING_YEAR
                    return
        elif context.user_data["state"] == IS_EDITING_YEAR:
            context.user_data["current_task"].set_deadline(2, message)
            month_key = await Admin.edit_deadline(step=1, year=int(message))
            x = await update.message.reply_text(Markup.choose_month, reply_markup=month_key)
            context.user_data["state"] = IS_EDITING_MONTH
            return
        elif context.user_data["state"] == IS_EDITING_MONTH:
            month_names = ["Jan", "Feb", "March", "Apr", "May", "June", "July", "Aug", "Sept", "Oct", "Nov", "Dec"]
            context.user_data["current_task"].set_deadline(1, month_names.index(message) + 1)
            day_key = await Admin.edit_deadline(step=2, year=context.user_data["current_task"].get_deadline()[2],
                                                month=message)
            x = await update.message.reply_text(Markup.choose_day, reply_markup=day_key)
            context.user_data["state"] = IS_EDITING_DAY
            return
        elif context.user_data["state"] == IS_EDITING_DAY:
            context.user_data["current_task"].set_deadline(0, int(message))
            await update.effective_message.reply_text(f"Set to {context.user_data["current_task"].get_deadline()}")
            context.user_data["state"] = IS_EDITING_TASK
            if not type(context.user_data["flag"]) == str:
                user_key = await Admin.edit_users(context.user_data["current_task"], symbol=app_data["button_texts"]["marked_symbol"][0])
                await update.message.reply_text(
                    f"{Markup.deadline_is_set_to} {context.user_data["current_task"].get_deadline()}",
                    reply_markup=Participant.CANCEL_MENU)
                await update.message.reply_text(Markup.attach_users, reply_markup=user_key)
                 
                context.user_data["state"] = IS_EDITING_ATTACHED_USERS
                return
        elif context.user_data["state"] == IS_EDITING_ATTACHED_USERS:
            pass
        elif context.user_data["state"] == IS_EDITING_TASK:
            await update.effective_message.delete()
        elif context.user_data["state"] == IS_CHANGING_PREFERENCES:
            if message == Markup.textual_content:
                context.user_data["flag"] = [True, 0, None]
                context.user_data["state"] = IS_CHANGING_textual_content
                if not context.user_data["current_task"]:
                    context.user_data["current_task"] = await  get_from_app_data(["textual_content", "button_texts"])
                await textual_content(update, context)
            elif message == Markup.alarm_interval:
                datum = (await get_from_app_data(["alarm_interval"]))["alarm_interval"]
                await update.effective_message.reply_text(f"{Markup.previous_alarm_set_to} {datum/3600}, {Markup.write_whole_numbers}", reply_markup=Participant.CANCEL_MENU)
                context.user_data["state"] = IS_CHANGING_REMINDER_INTERVAL
            elif message == Markup.admin_password:
                datum = (await get_from_app_data(["admin_password"]))["admin_password"]
                await update.effective_message.reply_text(f"{Markup.previous_password_set_to} {datum}, {Markup.password_should_be}", reply_markup=Participant.CANCEL_MENU)
                context.user_data["state"] = IS_CHANGING_ADMIN_PASSWORD
        elif context.user_data["state"] == IS_CHANGING_REMINDER_INTERVAL:
            if not message.isdigit():
                await update.effective_message.reply_text(f"{Markup.not_digit_or_whole_number}, {Markup.try_again}")
            else:
                interval = int(message) * 3600
                await set_app_data({"alarm_interval" : interval})
                reminder_job = None
                jobs = context.job_queue.jobs()
                for j in jobs:
                    if j.callback == reminder:
                        reminder_job = j
                
                if reminder_job:
                    reminder_job.schedule_removal()
                    reminder_job = None
                context.job_queue.run_repeating(reminder, interval=interval)
                await update.effective_message.reply_text(f"{Markup.alarm_set_to} {message} hours", reply_markup=Admin.PREFERENCES_MENU)
                context.user_data["state"] = IS_CHANGING_PREFERENCES
        elif context.user_data["state"] == IS_CHANGING_ADMIN_PASSWORD:
            if len(message) < Markup.min_password_len:
                await update.effective_message.reply_text(Markup.password_should_be)
            else:
                datum = {"admin_password" : message}
                await set_app_data(datum)
                await update.effective_message.reply_text(Markup.password_set_to, reply_markup=Admin.PREFERENCES_MENU)
                context.user_data["state"] = IS_CHANGING_PREFERENCES
        elif context.user_data["state"] == IS_CHANGING_textual_content:
            if context.user_data["flag"][2]:
                domain, key = context.user_data["flag"][2].split(".")
                context.user_data["current_task"][domain][key] = [message, context.user_data["current_task"][domain][key][1]]
                context.user_data["flag"][2] = None
                await update.effective_message.reply_text("Set")

    elif "+user" == user_type:
        if message == "Cancel":
            await update.message.reply_text(Markup.canceled, reply_markup=User.USER_MENU)
            context.user_data["state"] = IS_REGISTERED
            return
        if context.user_data["state"] == IS_REGISTERED:
            if message == Markup.task_list:
                await show_task_list(update, context, False, all_tasks=True)
            if message == Markup.my_tasks:
                await show_task_list(update, context, False, all_tasks=False)
    if context.user_data["state"] == IS_GUEST:
        if message == app_data["button_texts"]["user"][0]:
            context.user_data["flag"] = False
            context.user_data["state"] = IS_GIVING_NUMBER
            await show_registration_menu(update, context, menu_type="contact")
        if message == app_data["button_texts"]["admin"][0]:
            context.user_data["flag"] = True
            context.user_data["state"] = IS_GIVING_NUMBER
            await show_registration_menu(update, context, menu_type="contact")
        return
    elif context.user_data["state"] == IS_GIVING_NUMBER:
        if update.effective_message.contact.phone_number.removeprefix("+") in Admin.Super_Admin_Numbers:
            x = await update.message.reply_text(Markup.accepted_as_super, reply_markup=Admin.ADMIN_MENU)
            context.user_data["state"] = IS_REGISTERED
            await data_handler.add_new_user(update.effective_user.username,
                                            update.effective_message.contact.phone_number,
                                            update.effective_user.id, update.effective_user.full_name,
                                            True, True)
            return
        else:

            await data_handler.add_new_user(update.effective_user.username,
                                            update.effective_message.contact.phone_number,
                                            update.effective_user.id, update.effective_user.full_name,
                                            False, context.user_data["flag"])
        if not context.user_data["flag"]:
            await show_registration_menu(update, context, menu_type="applied")
            context.user_data["state"] = IS_WAITING_FOR_ACCEPTATION
        elif context.user_data["flag"]:
            await show_registration_menu(update, context, menu_type="password")
            context.user_data["state"] = IS_TYPING_PASSWORD
        context.user_data["flag"] = None
        return
    elif context.user_data["state"] == IS_TYPING_PASSWORD:
        if "admin" not in user_type:
            print("This admin is object of User")
        if message == Admin.Admin_Password:
            await show_registration_menu(update, context, menu_type="applied")
            context.user_data["state"] = IS_WAITING_FOR_ACCEPTATION
        return
    elif context.user_data["state"] == IS_ATTACHING_FILES:
        if message == Markup.save:
            # New Task
            if not context.user_data["flag"]:
                print("This is new task")
                context.user_data["state"] = IS_REGISTERED
                await update.message.reply_text(app_data["textual_content"]["files_set"][0], reply_markup=[User.USER_MENU, Admin.ADMIN_MENU][
                    "admin" in user_type])
                await data_handler.add_new_task(context.user_data["current_task"].to_tuple())
                context.user_data["current_task"] = None
                await data_handler.back_up(context)
            # Editing Task
            if context.user_data["flag"]:
                context.user_data["state"] = IS_REGISTERED
                x = await update.message.reply_text(app_data["textual_content"]["files_set"][0],
                                                    reply_markup=[User.USER_MENU, Admin.ADMIN_MENU][
                                                        "admin" in user_type])
                await data_handler.add_new_task(context.user_data["current_task"].to_tuple())
    elif context.user_data["state"] == IS_COMMENTING:
        context.user_data["current_task"].add_comment(user_id, message)
        await data_handler.add_new_task(context.user_data["current_task"].to_tuple())
        context.user_data["state"] = IS_REGISTERED
        x = await update.effective_message.reply_text(app_data["textual_content"]["commented"][0], reply_markup=[User.USER_MENU, Admin.ADMIN_MENU][
            "admin" in user_type])
        show_task_list(update, context, user_type=="+admin")


async def handle_inline_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query
    await data.answer()
    if  context.user_data["state"]==IS_REGISTERED:
        if update.effective_message.id not in context.user_data["cache"] :
            if not data.data[0] in '+-/*':
                print("Not in data")
                return
    
    

    

    user_id = update.effective_user.id
    user_type = await identify_participant(user_id, context)
    app_data = await get_from_app_data(["button_texts","textual_content"])

    print(f"Inline {data.data} hit")
    
    pattern = r'^[a-zA-Z]\d+$'

    if user_type == "+admin":
        # USER OR ADMIN ACCEPTATION
        if data.data[0] in ["+", "-", "*", "/"]:
            if "+" in data.data:
                await Admin.handle_ok_button(update, context, data.data)
            elif "-" in data.data:
                await Admin.handle_no_button(update, context, data.data)
            elif "*" in data.data:
                a = data.data.removeprefix("*")
                await data_handler.del_a_task(a)
                await update.effective_message.delete()
                await update.effective_message.reply_text(Markup.deleted)
                print(context.user_data["cache"])
                if a in context.user_data["cache"]:
                    await clean(context, a, user_id, True)
            elif "/" in data.data:
                await update.effective_message.delete()
                await update.effective_message.reply_text(Markup.you_can_delete)
        if context.user_data["state"] == IS_EDITING_ATTACHED_USERS:
            if data.data == "OK":
                # ATTACHED USERS EDITING
                if type(context.user_data["flag"]) == str:
                    await update.effective_message.edit_reply_markup(Admin.EDIT_MENU)
                    await update.effective_message.reply_text("Set")
                    context.user_data["state"] = IS_EDITING_TASK

                    # NOT EDITING, CREATING A NEW TASK
                elif type(context.user_data["flag"]) != str:
                    context.user_data["state"] = IS_ATTACHING_FILES
                    x = await update.effective_message.reply_text(app_data["textual_content"]["file_attach_prompt"][0],
                                                                  reply_markup=Participant.ATTACH_FILE_MENU)
            else:
                # ADMIN IS RADIO BUTTONING USERS
                user_list = await Admin.edit_users(context.user_data["current_task"], int(data.data), app_data["button_texts"]['marked_symbol'][0])
                await update.effective_message.edit_reply_markup(user_list)
        if context.user_data["state"] == IS_EDITING_TASK:
            if "des" == data.data:
                context.user_data["state"] = IS_EDITING_DESCRIPTION
                x = await update.effective_message.reply_text(Markup.input_description, reply_markup=Admin.CANCEL_MENU)
                return
            elif "dea" == data.data:
                year_menu = await Admin.edit_deadline(step=0)
                x = await update.effective_message.reply_text(Markup.choose_year, reply_markup=year_menu)
                context.user_data["state"] = IS_EDITING_YEAR
                return
            elif "use" == data.data:
                user_key = await Admin.edit_users(context.user_data["current_task"], symbol=app_data["button_texts"]['marked_symbol'])
                await update.effective_message.edit_reply_markup(user_key)
                context.user_data["state"] = IS_EDITING_ATTACHED_USERS
                return
            elif "del" == data.data:
                await update.effective_message.edit_reply_markup(reply_markup=Participant.INLINE_DIALOG)
            elif "don" == data.data:
                await data_handler.add_new_task(context.user_data["current_task"].to_tuple())
                context.user_data["flag"] = None
                context.user_data["state"] = IS_REGISTERED
                context.user_data["lastly_notified"] = None
                context.user_data["current_task"] = None
                await clean(context, None, user_id)
                await data_handler.back_up(context)
                await update.effective_message.reply_text(Markup.edited, reply_markup=Admin.ADMIN_MENU)
            elif "can" == data.data:
                context.user_data["flag"] = None
                context.user_data["state"] = IS_REGISTERED
                context.user_data["lastly_notified"] = None
                context.user_data["current_task"] = None
        if context.user_data["state"] == IS_CHANGING_textual_content:
            if data.data == "next":
                context.user_data["flag"][1]+=1
                await textual_content(update, context)
            elif data.data == "prev":
                context.user_data["flag"][1]-=1
                await textual_content(update, context)
            elif data.data == "save":
                await set_app_data(context.user_data["current_task"])
                context.user_data["current_task"] = None
                context.user_data["flag"] = None
                context.user_data["state"] = IS_CHANGING_PREFERENCES
                await update.effective_message.delete()
                await update.effective_message.reply_text(Markup.saved, reply_markup=Admin.PREFERENCES_MENU)
            elif data.data == "disc":
                await update.effective_message.edit_text(Markup.are_you_sure)
                await update.effective_message.edit_reply_markup(Admin.INLINE_DIALOG)
            elif data.data not in ["yes", "no"]:
                await textual_content(update, context, data.data)          
    if user_type == "+user":
        pass
    if re.match(pattern, data.data):
        # EDITING
        all_tasks = await data_handler.get_all_tasks()
        task = (data.data[1::], *all_tasks[data.data[1::]])
        context.user_data["current_task"] = Task(*task)
        if user_type == "+admin":
            context.user_data["lastly_notified"] = {}
            context.user_data["lastly_notified"][context.user_data["current_task"].get_id()] = False
        if "e" in data.data and user_type == "+admin":
            context.user_data["state"] = IS_EDITING_TASK
            context.user_data["flag"] = data.data.removeprefix("e")
            x = await update.effective_message.edit_reply_markup(reply_markup=Admin.EDIT_MENU)
            await clean(context, x.message_id, user_id)
        elif "n" in data.data and user_type == "+admin":
            if not context.user_data["lastly_notified"][context.user_data["current_task"].get_id()]:
                await notify_users(context, context.user_data["current_task"].get_attached_users(), "reminder",
                                   data=f"It ends on {context.user_data["current_task"].get_deadline(True)}")
                a = (await context.user_data["current_task"].show_me(app_data,True, user_id, True))[1]
                await update.effective_message.edit_reply_markup(reply_markup=a)
                context.user_data["lastly_notified"] = True
        elif "c" in data.data and context.user_data["cache"]:
            await clean(context, update.effective_message.id, user_id)
            await update.effective_message.reply_text(app_data["textual_content"]["write_comment_prompt"][0])
            context.user_data["state"] = IS_COMMENTING
        elif "f" in data.data and context.user_data["cache"]:
            await clean(context, update.effective_message.id, user_id)
            x = await update.effective_message.reply_text(app_data["textual_content"]["file_attach_prompt"][0], reply_markup=Participant.ATTACH_FILE_MENU)
            context.user_data["state"] = IS_ATTACHING_FILES
        elif "a" in data.data:
            context.user_data["flag"] = "acc"
            await update.effective_message.edit_reply_markup(Participant.INLINE_DIALOG)
        elif "z" in data.data:
            if user_id in context.user_data["current_task"].get_accepted_users():
                context.user_data["flag"] = "com"
                await update.effective_message.edit_reply_markup(Participant.INLINE_DIALOG)
            else:
                await update.effective_message.edit_reply_markup(
                    await context.user_data["current_task"].show_me(app_data, user_id=user_id, for_markup_edit=True,
                                                                    light_accept=True))
    elif data.data == "yes":
        # for deleting task
        if type(context.user_data["flag"]) == str and context.user_data["flag"].isdigit():
            await data_handler.del_a_task(context.user_data["flag"])
            await clean(context, update.effective_message.id, user_id, inverse=True)
            await update.effective_message.reply_text(Markup.yes)
            context.user_data["flag"] = None
            context.user_data["current_task"] = None
            context.user_data["lastly_notified"] = None
            context.user_data["state"] = IS_REGISTERED
        # for accepting task
        elif context.user_data["flag"] in ["acc", "com"]:
            if context.user_data["flag"] == "acc":
                context.user_data["current_task"].add_accepted_user(user_id)
            else:
                context.user_data["current_task"].add_completed_user(user_id)
                if set(context.user_data["current_task"].get_completed_users()) == set(
                        context.user_data["current_task"].get_attached_users()):
                    await notify_admins(context, user_id, "task_is_done",
                                        args=[context.user_data["current_task"].get_id()])
            await data_handler.add_new_task(context.user_data["current_task"].to_tuple())
            markup = (await  context.user_data["current_task"].show_me(app_data,False, user_id, False, for_markup_edit=True))
            await update.effective_message.edit_reply_markup(markup)
            context.user_data["current_task"] = None
            context.user_data["flag"] = None
            await data_handler.back_up(context)
        # for discarding textual content modification
        elif context.user_data["state"] == IS_CHANGING_textual_content:
            await update.effective_message.delete()
            context.user_data["current_task"] = None
            context.user_data["flag"] = None
            context.user_data["state"] = IS_CHANGING_PREFERENCES
            await update.effective_message.reply_text(Markup.discarded, reply_markup=Admin.PREFERENCES_MENU)
    elif data.data == "no":
        # for deleting task
        if type(context.user_data["flag"]) == str and context.user_data["flag"].isdigit():
            await update.effective_message.edit_reply_markup(reply_markup=Admin.EDIT_MENU)
        elif context.user_data["flag"] in ["acc", "com"]:
            await update.effective_message.edit_reply_markup(
                reply_markup=(await context.user_data["current_task"].show_me(app_data,for_markup_edit=True )))
            context.user_data["current_task"] = None
            context.user_data["flag"] = None
        # for discarding textual content modification
        elif context.user_data["state"] == IS_CHANGING_textual_content:
            await update.effective_message.edit_text("Change")
            await update.effective_message.edit_reply_markup(await textual_content(update, context, only_markup=True))
            

async def handle_file_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await identify_participant(user_id, context)
    if context.user_data["state"] == IS_ATTACHING_FILES:
        doc = update.effective_message.document
        img = update.effective_message.photo
        if doc:
            context.user_data["current_task"].add_file(user_id, doc.file_id)
        elif img:
            img = img[-1]
            context.user_data["current_task"].add_file(user_id, img.file_id)


async def textual_content(update: Update, context: ContextTypes.DEFAULT_TYPE, data=None, only_markup=False):
    
    keyboard_data = {}
    column_height = Markup.column_len
    is_first_time, page, key = context.user_data["flag"]
    

    for domain, values in context.user_data["current_task"].items():
        for k, v in values.items():
            keyboard_data[k] = v + [domain]
    
    if not data:
        keys0 = list(keyboard_data.keys())
        if page <0:
            context.user_data["flag"][1] = 0
            return
        if page > int(len(keys0)/column_height)  :
            context.user_data["flag"][1] = int(len(keys0)/column_height)
            return
        keys = keys0[page*column_height: (page+1)*column_height]
        keyboard = [[InlineKeyboardButton(i, callback_data=i)] for i in keys]
        keyboard += [[InlineKeyboardButton(Markup.prev, callback_data="prev"), InlineKeyboardButton(Markup.next, callback_data="next")]]
        keyboard += [[InlineKeyboardButton(Markup.save, callback_data="save"), InlineKeyboardButton(Markup.discard, callback_data="disc")]]
        markup = InlineKeyboardMarkup(keyboard)
        if only_markup:
            return markup
        if is_first_time:
            await update.effective_message.reply_text(Markup.what_change, reply_markup=markup)
            context.user_data["flag"] = [False, page, None]
        else:
            await update.effective_message.edit_reply_markup(markup)
    elif data:
        domain = keyboard_data[data][-1]
        message = f"{keyboard_data[data][1]}. {Markup.previous_is} {keyboard_data[data][0]}"
        await update.effective_message.reply_text(message, reply_markup=ReplyKeyboardRemove())
        context.user_data["flag"][2] = f"{domain}.{data}"


async def show_registration_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, menu_type: str,
                                 user_id: int = None):
    # It suggests a registration interface
    # There are only 2 interfaces:
    # 1) Registration
    # 2) Main
    app_data =await  get_from_app_data(["textual_content", "button_texts"])
    if not user_id:
        user_id = update.effective_user.id
    keyboard = None
    message = None
    if menu_type == "type":
        message = app_data["textual_content"]["greeting_message"][0]
        keyboard = [[KeyboardButton(app_data["button_texts"]["user"][0]), KeyboardButton(app_data["button_texts"]["admin"][0])]]
    elif menu_type == "contact":
        message = app_data["textual_content"]["phone_number_prompt"][0]
        keyboard = [[KeyboardButton(app_data["button_texts"]["share_number"][0], request_contact=True)]]
    elif menu_type == "password":
        message = app_data["textual_content"]["admin_password_prompt"][0]
        pass
    elif menu_type == "applied":
        message = app_data["textual_content"]["application_sent"][0]
        keyboard = None
        await notify_admins(context, update.effective_user.id, "acceptance")
    elif menu_type == "waiting":
        message = app_data["textual_content"]["appliaction_waiting"][0]
        keyboard = None
    if keyboard:
        markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    else:
        markup = ReplyKeyboardRemove()
    await context.bot.sendMessage(user_id, message, reply_markup=markup)


async def notify_users(context: ContextTypes.DEFAULT_TYPE, users_list, not_type, data=None):
    # This function is responsible for sending different messages
    # and notifications to users
    app_data = await  get_from_app_data(["textual_content"])
    if not_type == "reminder":
        for i in users_list:
            await context.bot.sendMessage(i, f"{app_data["textual_content"]["user_notification"][0]} \n{data}")


async def reminder(context):
    tasks = await data_handler.get_all_tasks()
    app_data = await get_from_app_data(["textual_content"])
    all_users = []
    for i in tasks.values():
        all_users.extend(i[3])
        all_users =list( set(all_users) - set(i[5]))
    for user_id in all_users:
        await context.bot.sendMessage(user_id, app_data["textual_content"]["user_reminder"][0])


async def notify_admins(context: ContextTypes.DEFAULT_TYPE, user_id: int, type_: str, args: list = None):
    # This function is responsible for sending different messages
    # and notifications to admins
    all_users = await  data_handler.get_all_users()
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
        yes_key = InlineKeyboardButton(Markup.ok, callback_data=f"+{user_id}")
        no_key = InlineKeyboardButton(Markup.no, callback_data=str(-user_id))
    elif type_ == "task_is_done":
        message = Markup.task_is_complete
        yes_key = InlineKeyboardButton(Markup.ok, callback_data=f"*{args[0]}")
        no_key = InlineKeyboardButton(Markup.no, callback_data=f"/{args[0]}")
    for admin_id, data in all_users["admins"].items():
        if yes_key and no_key:
            markup = InlineKeyboardMarkup([[yes_key, no_key]])
            await context.bot.sendMessage(admin_id, message, reply_markup=markup)


async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # All commands are operated here
    user_id = update.effective_user.id
    await identify_participant(user_id, context)
    app_data = await  get_from_app_data(["textual_content", "alarm_interval"])
    user_type = await data_handler.check_if_user_exists(user_id)
    command = update.message.text[1:]

    if command == "start":
        if user_type == "+admin":
            x = await update.message.reply_text(app_data["textual_content"]["start_after_registration"][0], reply_markup=Admin.ADMIN_MENU)
            jobs = context.job_queue.jobs()
            for j in jobs:
                if j.callback == reminder:
                    continue
                context.job_queue.run_repeating(reminder, app_data["alarm_interval"])  
             
            context.user_data["state"] = IS_REGISTERED
        elif user_type == "-admin":
            await update.message.reply_text(app_data["textual_content"]["appliaction_waiting"][0])
        elif user_type == "+user":
            x = await update.message.reply_text(app_data["textual_content"]["start_after_registration"][0], reply_markup=User.USER_MENU)
             
            context.user_data["state"] = IS_REGISTERED
        elif user_type == "-user":
            await update.message.reply_text(app_data["textual_content"]["appliaction_waiting"][0])
        else:
            context.user_data["state"] = IS_GUEST
            await update.message.reply_text(app_data["textual_content"]["start_after_registration"][0])
            await show_registration_menu(update, context, "type")


def graceful_shutdown():
    print("Shutting Down...")
    data_handler.Data.app_data = APP_DATA
    data_handler.emergency_save()
    sys.exit()


async def post_polling(app: Application):
    global APP_DATA
    print("Setting schedule...")
    await data_handler.recover()
    app.job_queue.run_repeating(data_handler.back_up, interval=BACKUP_INTERVAL, first=FIRST_BACKUP)
    APP_DATA = await data_handler.get_app_data()



def launch_bot(token=TOKEN, admin_number: str = None, dashboard_url = None):
    global DASHBOARD_URL
    # Very first, core function that initiates bot.
    # This function is called only once in the whole bot lifetime

    atexit.register(graceful_shutdown)
    #signal.signal(signal.SIGTERM, graceful_shutdown)

    app = Application.builder()
    app.token(token)

    app.read_timeout(READ_TIMEOUT)
    app.write_timeout(WRITE_TIMEOUT)
    app.post_init(post_polling)
    app = app.build()

    if admin_number:
        Admin.Super_Admin_Numbers.append(admin_number)
    if dashboard_url:
        DASHBOARD_URL = dashboard_url
        print(DASHBOARD_URL)

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
