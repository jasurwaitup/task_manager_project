# Task Manager Bot created for TTPU adminstration


It faciliates effective communication between directors and employees 
allowing to assign and complet toe tasks.

Managers, thereinafter admins, can:
- create and edit tasks
- remind users about tasks
- acces dashboard
- accept new users or admins
- customize bot's UI
- attach files and add comments


Employees, thereinafter users, can:
- complete tasks
- attach files and add comments



>[!IMPORTANT]
>### How to use this program:
>1. Make sure you have properly installed python, adding it to PATH[^1]
>2. Make sure you have a vacant bot and its token (don't forget about adding /start command)
>3. Your bot shouldnt be restricted or banned
>4. You should have ngrok (https://ngrok.com/) account and authtoken from it
>5. Internet connection is required
>6. Find 'start.bat' in the same directory as readme file, and run it
>8. It automatively installs all the dependences
>9. It asks you super admins[^2] phone number, bot token and authtoken
>10. After sucessful initalization bots starts operating

>[!TIP]
> ## How to use Bot:
>- After starting (/start) bot asks if the guest is an admin or a user
>- The next step involves sharing phone number
>- If the phone number matches with the super admin phone number, the guest directly becomes an admin
>- All the other candidatorial admins required to enter passworrd supplemented by rector
>- Users are not aksed any passwords
>- Then it depends solely on current admins whether to accept or reject potential admin/user
>- After acceptation, launches main functionality of the bot listed earlier

>[!NOTE]
>You can change bot token,first admins phone number and authtoken
in config.json if you want to restart bot with different
settings. However, if you don't have any clue about json files,
or programming as a whole, for God's sake, please don't touch
ANYTHING except start.bat and readme. If you don't understand or face any problems during installation,
please consult IT specialist

[^1]: It is accomplished by custom installation of python, tap the "add to PATH" flag after selecting custom installation.
[^2]: Super admin is the first admin of the bot.

Created by: Jasurbek Mahmudjonov

Company: TTPU

Contact: +998505750117

Email: jasur.prsnl@gmail.com


Special thanks to:

- Open AI, ChatGpt
- Reddit users
- Stack Overflow users
- Microsoft VS Code
- PyCharm community
- Turin Wi-Fi and computers (I appreciate the support)
