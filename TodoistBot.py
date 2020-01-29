import configparser
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, CommandHandler, CallbackQueryHandler, Filters
from APIHandler import APIHandler


class TodoistBot:
    class Flags:
        new_project = False
        new_task = False
        select_project_for_task = False

        def __init__(self, flag=False):
            self.new_project = flag
            self.new_task = flag
            self.select_project_for_task = flag

    flags = Flags()

    def __init__(self):
        self.next_action = ""
        # Read Configs from file
        config = configparser.ConfigParser()
        config.read("config.ini")

        # set Telegram bot token
        bot_token = config['telegram']['bot_token']
        # set Todoist API token
        api_token = config['todoist']['api_token']
        # set Todoist API URL
        api_url = config['todoist']['api_url']

        # initiate a Telegram updater instance
        self.updater = Updater(bot_token)

        # initiate a Todoist API handler
        self.api = APIHandler(api_token, api_url)

    @staticmethod
    def read_config():
        # Reading Configs
        config = configparser.ConfigParser()
        config.read("config.ini")
        return config

    @staticmethod
    def task_button_markup(tasks):
        keyboard = []
        for task in tasks:
            keyboard.append(
                [InlineKeyboardButton(task['content'], url=task['url'], callback_data=task['id'])])

        markup = InlineKeyboardMarkup(keyboard)
        return markup

    def button(self, bot, update):
        query = update.callback_query

        if self.next_action == "get_tasks_by_project":
            bot.edit_message_text(text="project task list",
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id)
            self.show_tasks_by_project(bot, format(query.data), query.message.chat_id)
            self.next_action = None

    def show_tasks_by_project(self, bot, project_id, chat_id):
        tasks_list = self.api.get_tasks_by_project(project_id)
        if len(tasks_list) > 0:
            reply_markup = self.task_button_markup(tasks_list)
            bot.send_message(chat_id=chat_id, text="click on any task to show task details", reply_markup=reply_markup)
        else:
            bot.send_message(chat_id=chat_id, text="no tasks for this project")
            self.flags.__init__()

    def projects(self, bot, update):
        chat_id = update.message.chat_id
        project_list = self.api.get_project_list()

        keyboard = []
        for project in project_list:
            keyboard.append(
                [InlineKeyboardButton(project['name'], callback_data=project['id'])])

        reply_markup = InlineKeyboardMarkup(keyboard)
        self.next_action = "get_tasks_by_project"
        bot.send_message(chat_id=chat_id, text="Choose a Project to see tasks list", reply_markup=reply_markup)

    def all_tasks(self, bot, update):
        chat_id = update.message.chat_id
        tasks_list = self.api.get_all_tasks()

        if len(tasks_list) > 0:
            reply_markup = self.task_button_markup(tasks_list)
            bot.send_message(chat_id=chat_id, text="click on any task to show task details", reply_markup=reply_markup)
        else:
            bot.send_message(chat_id=chat_id, text="no tasks in your list")

    def today_task(self, bot, update):
        chat_id = update.message.chat_id
        today_tasks = self.api.get_today_tasks()
        if len(today_tasks) > 0:
            reply_markup = self.task_button_markup(today_tasks)
            bot.send_message(chat_id=chat_id, text="click on any task to show task details", reply_markup=reply_markup)
        else:
            bot.send_message(chat_id=chat_id, text="no tasks for today")

    def new_project(self, bot, update):
        chat_id = update.message.chat_id
        self.flags.new_project = True
        bot.send_message(chat_id=chat_id, text="enter name for new project")

    def new_task(self, bot, update):
        chat_id = update.message.chat_id
        self.flags.new_task = True
        bot.send_message(chat_id=chat_id, text="enter name for new task")

    def general_handler(self, bot, update):
        chat_id = update.message.chat_id
        text = update.message.text

        if self.flags.new_project:
            if self.api.create_project(text):
                bot.send_message(chat_id=chat_id, text="project created: " + text)
        if self.flags.new_task:
            if self.api.create_task(text):
                bot.send_message(chat_id=chat_id, text="task created: " + text)

    def main(self):
        updater = self.updater
        dp = updater.dispatcher

        # Add command handlers
        dp.add_handler(CommandHandler('projects', self.projects))
        dp.add_handler(CommandHandler('newproject', self.new_project))
        dp.add_handler(CommandHandler('tasks', self.all_tasks))
        dp.add_handler(CommandHandler('today', self.today_task))
        dp.add_handler(CommandHandler('newtask', self.new_task))

        # Add callback handlers for buttons
        updater.dispatcher.add_handler(CallbackQueryHandler(self.button))

        # general message handler
        updater.dispatcher.add_handler(MessageHandler(Filters.all, self.general_handler))

        updater.start_polling()
        updater.idle()
