from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime

from functionality import Markup, radio_button
import data_handler

class Task:
    def __init__(self, task_id : str = None,  description : str = None, deadline : list = None, started_on : list = None, attached_users : list = None,
                 users_accepted : list = None, users_completed : list = None,attached_files : dict = None,
                 comments : dict = None):
        self._task_id = [datetime.now().strftime("%y%m%d%H%M%S"), task_id][not task_id is None]
        self._description = description
        if deadline:
            self._deadline = deadline
        else:
            self._deadline = [None, None, None]
        y,m,d = self._task_id[0:2], self._task_id[2:4], self._task_id[4:6]
        x =  [int(d), int(m), int(y)]
        self._started_on = [x, started_on][not started_on is None]
        self._attached_users = [[], attached_users][not attached_users is None]
        self._users_accepted = [[], users_accepted][not users_accepted is None]
        self._users_completed = [[], users_completed][not users_completed is None]
        self._attached_files = [{}, attached_files][not attached_files is None]
        self._comments = [{}, comments][not comments is None]


    def get_id(self):
        return self._task_id
    def set_description(self, description : str):
        self._description = description
    def get_description(self):
        return self._description
    def set_deadline(self,position:int, value):
        if type(value) == str:
            self._deadline[position] = int(value)
        elif type(value) == int:
            self._deadline[position] = value
    def get_deadline(self, as_str = False):
        if as_str:
            return ".".join(map(str,self._deadline))
        return self._deadline
    def add_comment(self, user_id, comment):
        user_id = str(user_id)
        if user_id in self._comments.keys():
            self._comments[user_id].append(comment)
        else:
            self._comments[user_id] = [comment]
    def add_file(self, user_id, file_id):
        user_id = str(user_id)
        if user_id in self._attached_files.keys():
            self._attached_files[user_id].append(file_id)
        else:
            self._attached_files[user_id] = [file_id]
    def get_files(self):
        return self._attached_files
    def add_user(self, user_id):
        self._attached_users.append(user_id)
    def add_accepted_user(self, user_id) -> bool:
        if not user_id in self._users_accepted:
            self._users_accepted.append(user_id)
            return True
        else:
            return False
    def add_completed_user(self, user_id) ->bool:
        if not user_id in self._users_completed:
            self._users_completed.append(user_id)
            return True
        else:
            return False
    def del_user(self, user_id):
        if user_id in self._attached_users:
            self._attached_users.remove(user_id)
        if user_id in self._users_accepted:
            self._users_accepted.remove(user_id)
        if user_id in self._users_completed:
            self._users_completed.remove(user_id)
    def get_attached_users(self):
        return self._attached_users
    def get_completed_users(self):
        return self._users_completed
    def get_accepted_users(self):
        return self._users_accepted
    def get_comments(self):
        return self._comments
    def to_tuple(self):
        a = (self._task_id, self._description, self._deadline, self._started_on, self._attached_users,
             self._users_accepted, self._users_completed, self._attached_files, self._comments)
        return a
    def from_tuple(self, data):
        self.__init__(*data)

    async def show_me(self, app_data, is_for_admin : bool = False, user_id = None, notified_flag = False, light_accept = False ,for_markup_edit = False, all_users:dict = None):
        print("show_me")
        comment_button = InlineKeyboardButton(app_data["button_texts"]["comment"][0], callback_data=f"c{self._task_id}")
        file_button = InlineKeyboardButton(app_data["button_texts"]["file"][0], callback_data=f"f{self._task_id}")
        if is_for_admin:
            a = app_data["button_texts"]["notify"][0]
            b = "n"
            if notified_flag:
                a = "Notified"
                b = "N"
            notify_button = InlineKeyboardButton(a, callback_data=f"{b}{self._task_id}")
            edit_button = InlineKeyboardButton(app_data["button_texts"]["edit"][0], callback_data=f"e{self._task_id}")
            markup = InlineKeyboardMarkup([[file_button, comment_button], [notify_button, edit_button]])
        else:
            a = app_data["button_texts"]["accept"][0]
            if light_accept:
                h = app_data["button_texts"]["highlight_symbol"][0]
                a = f"{h}{a}{h}"
            b = "a"
            c = app_data["button_texts"]["complete"][0]
            d = "z"
            if user_id in self._users_accepted:
                a = "Accepted"
                b = "A"
            if user_id in self._users_completed:
                c = "Completed"
                d = "Z"
            accept_button = InlineKeyboardButton(a, callback_data=f"{b}{self._task_id}")
            complete_button = InlineKeyboardButton(c, callback_data=f"{d}{self._task_id}")
            markup = InlineKeyboardMarkup([[file_button, comment_button], [accept_button, complete_button]])

        if not for_markup_edit:
            users_list = []
            for u in self._attached_users:
                if u in self._users_completed:
                    users_list.append(f"{u} {app_data["button_texts"]["completed_symbol"][0]}")
                elif u in self._users_accepted:
                    users_list.append(f"{u} {app_data["button_texts"]["accepted_symbol"][0]}")
                else:
                    users_list.append(f"{u} {app_data["button_texts"]["attached_symbol"][0]}")
            body = f"{self._description}\n\n"
            a = ".".join(map(str, self._started_on))
            b = ".".join(map(str, self._deadline))
            body += f"Started on: {a}\n"
            body +=  f"Ends on: {b}\n"
            if not all_users:
                all_users = await data_handler.get_all_users()
            new_users_list = []
            for e in users_list:
                u_id = e.split(" ")[0]
                u_id = int(u_id)
                name = all_users["users"][u_id][2]
                a = e.split(" ")[-1]
                new_users_list.append(f"{name} {a}")
            body += "\n"
            body += "\n".join(new_users_list)
            return body, markup
        else:
            return markup


class Participant:
    CANCEL_KB = [[
        KeyboardButton(Markup.cancel)]
    ]

    ATTACH_FILE_KB = [[KeyboardButton(Markup.save)],[
        KeyboardButton(Markup.cancel)]
    ]

    INLINE_DIALOG_KB = [
        [InlineKeyboardButton(Markup.yes, callback_data="yes")],
        [InlineKeyboardButton(Markup.no, callback_data="no")]
    ]
    INLINE_DIALOG = InlineKeyboardMarkup(INLINE_DIALOG_KB)

    CANCEL_MENU = ReplyKeyboardMarkup(CANCEL_KB, resize_keyboard=True, one_time_keyboard=True)
    ATTACH_FILE_MENU = ReplyKeyboardMarkup(ATTACH_FILE_KB, resize_keyboard=True, one_time_keyboard=True)
    def __init__(self, user_id : int = None,  phone_number : str = None, username : str = None, full_name : str = None):
        self._user_id = user_id
        self._username = username
        self._user_phone_number = phone_number
        self._user_full_name = full_name
        self._user_is_activated = False
    def attach_file(self):
        pass
    def handle_attach_file_button(self):
        pass
    def show_task_list(self):
        pass
    def activate(self):
        self._user_is_activated = True
    def is_activated(self):
        return self._user_is_activated


class User(Participant):
    USER_MENU_KB = [[
        KeyboardButton(Markup.task_list)],
        [KeyboardButton(Markup.my_tasks)]
    ]
    USER_MENU = ReplyKeyboardMarkup(USER_MENU_KB, resize_keyboard=True)


class Admin(Participant):
    Super_Admin_Numbers = ["998889650117"]
    Admin_Password = None
    ADMIN_MENU_KB = [
        [KeyboardButton(Markup.task_list)],
        [KeyboardButton(Markup.new_task)],
        [KeyboardButton(Markup.pref)]
    ]
    ADMIN_MENU = ReplyKeyboardMarkup(ADMIN_MENU_KB, resize_keyboard=True, one_time_keyboard=True)

    EDIT_KB = [[InlineKeyboardButton("Description", callback_data="des")],
               [InlineKeyboardButton("Deadline", callback_data="dea")],
               [InlineKeyboardButton("Users", callback_data="use")],
               [InlineKeyboardButton("Delete", callback_data="del")],
                [InlineKeyboardButton("Done", callback_data="don")],
               [InlineKeyboardButton("Back", callback_data="can")]]
    EDIT_MENU  = InlineKeyboardMarkup(EDIT_KB)

    PREFERENCES_KB = [

        [KeyboardButton("Alarm Interval")],
        [KeyboardButton("Admin Password")],
        [KeyboardButton("Textual Content")],
        [KeyboardButton(Markup.cancel)]
    ]
    PREFERENCES_MENU = ReplyKeyboardMarkup(PREFERENCES_KB, resize_keyboard=True)

    @staticmethod
    async def handle_ok_button( update : Update, context : ContextTypes.DEFAULT_TYPE, data):
        user_id = int(data)
        is_admin = False
        if user_id in (await data_handler.get_all_users())["admins"]:
            is_admin = True
        await data_handler.accept_user(user_id, True, is_admin)
        await context.bot.sendMessage(user_id, "You're accepted", reply_markup=[User.USER_MENU, Admin.ADMIN_MENU][is_admin])
        await update.effective_message.delete()
    @staticmethod
    async def handle_no_button( update : Update, context : ContextTypes.DEFAULT_TYPE, data):
        user_id = -int(data)
        is_admin = False
        if user_id in (await  data_handler.get_all_users())["admins"]:
            is_admin = True
        await data_handler.accept_user(user_id, False, is_admin)
        await context.bot.sendMessage(user_id, "You're rejected", reply_markup=ReplyKeyboardRemove())
        await update.effective_message.delete()
    @staticmethod
    async def edit_users(a_task : Task, user_id=None):
        chosen = a_task.get_attached_users()
        full_data = (await data_handler.get_all_users())["users"]
        full_dict = {}
        for k, v in full_data.items():
            full_dict[k] = v[-2]
        return await radio_button(chosen, full_dict, user_id)
    @staticmethod
    async def edit_deadline (step : int, year : int =None, month : str=None):
        month_names = ["Jan", "Feb", "March", "Apr", "May", "June", "July", "Aug", "Sept", "Oct", "Nov", "Dec"]
        c_day, c_month, c_year = datetime.now().strftime("%d/%m/%y").split("/")
        c_day, c_month, c_year = int(c_day), int(c_month), int(c_year)
        def days_in_months(i_year):
            return [31, 28 + i_year%4==0, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if step == 0:
            years = list(range(c_year, c_year + 2))
            keys = [[KeyboardButton(str(i)) for i in years], ["Cancel"]]
            keyboard = ReplyKeyboardMarkup(keys, resize_keyboard=True, one_time_keyboard=True)
            return keyboard
        elif step == 1:
            keys = []
            if year != c_year:
                keys = [[KeyboardButton(i) for i in month_names[0:4]],
                    [KeyboardButton(i) for i in month_names[4:8]],
                    [KeyboardButton(i) for i in month_names[8:]]]
            elif year == c_year:
                a = c_month
                if days_in_months(year)[c_month-1] - c_day > 0:
                    a = c_month - 1
                month_names  = month_names[a:]
                for i in range((len(month_names)/4).__ceil__()):
                    keys = [[KeyboardButton(i) for i in month_names[i*4:(i+1)*4:1]]]
            keys.append(["Cancel"])
            keyboard = ReplyKeyboardMarkup(keys, resize_keyboard=True)
            return keyboard
        elif step==2:
            month = month_names.index(month)
            if year == c_year and month+1 == c_month:
                days = range(c_day+1, days_in_months(year)[month] + 1)
            else:
                days = range(1, days_in_months(year)[month] + 1)
            keys = []
            print(days)
            for i in range((len(days)/7).__ceil__()):
                keys.append([KeyboardButton(i) for i in days[i*7:(i+1)*7:1]])
            keys[-1].append("Cancel")
            keyboard = ReplyKeyboardMarkup(keys, resize_keyboard=True)
            return keyboard
        elif step ==3:
            pass
           






