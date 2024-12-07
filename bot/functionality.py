from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class Markup:
    min_password_len = 6
    column_len = 8
    all_tasks = "All Tasks"
    no_tasks = "No tasks yet"
    cancel = "Cancel"
    canceled = "Canceled"
    input_description = "Input Description"
    what_change = "What would you like to change"
    choose_year = "Choose year"
    choose_month = "Choose month"
    choose_day = "Choose day"
    deadline_is_set_to = "Deadline is set to"
    attach_users = "Attach users"
    textual_content = "Textual Content"
    alarm_interval = "Alarm Interval"
    admin_password = "Admin Password"
    previous_alarm_set_to = "Previous alarm was"
    previous_password_set_to = "Previous passord was"
    write_whole_numbers = "Write whole numbers"
    password_should_be = f"At least {min_password_len} characters"
    not_digit_or_whole_number = "Not digit or whole number"
    try_again = "try again"
    alarm_set_to = "Interval is set to"
    password_set_to = "Password is set"
    accepted_as_super = "You are accepted as super Admin"
    you_can_delete = "Left, you can delete it later"
    ok = "Ok"
    yes = "yes"
    no = "no"
    deleted = "Deleted"
    edited = "Edited"
    next = "next"
    prev = "prev"
    save = "save"
    discard = "disc"
    saved = "Saved"
    are_you_sure = "Are you Sure"
    discarded = "Discarded"
    previous_is = "Previous is :"
    task_is_complete = "Task is complete, delete the task?"
    new_task = "New Task"
    task_list = "Task List"
    my_tasks = "My Tasks"
    pref = "Preferences"
    dashboard = "Dashboard"

async def radio_button(chosen_list:list, full_dict:dict, hit_button = None):
    #elements in chosen list are keys for full_dict
    if hit_button:
        if hit_button not in chosen_list:
            chosen_list.append(hit_button)
        else:
            chosen_list.remove(hit_button)
    kb = []
    for button, name in full_dict.items():
        mark = ""
        if button in chosen_list:
            mark = "V"
        kb.append([InlineKeyboardButton(f"{mark} {name}", callback_data=button)])
    kb.append([InlineKeyboardButton("Ok", callback_data="OK")])
    radio_menu= InlineKeyboardMarkup(kb)
    return radio_menu