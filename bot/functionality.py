from telegram import InlineKeyboardButton, InlineKeyboardMarkup

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