from todoist.api import TodoistAPI
import requests
from datetime import datetime
import uuid
import json


class APIHandler:

    def __init__(self, api_token):
        # initiate a todoist api instance
        self.api = TodoistAPI(api_token)
        self.api_token = api_token

    def get_project_list(self):
        self.api.sync()
        project_list = self.api.state['projects']
        return project_list

    def get_tasks_by_project(self, project_id):
        tasks_list = requests.get(
            "https://beta.todoist.com/API/v8/tasks",
            params={
                "project_id": project_id
            },
            headers={
                "Authorization": "Bearer %s" % self.api_token
            }).json()

        return tasks_list

    def create_project(self, project_name):
        self.api.projects.add(project_name)
        self.api.commit()
        return True

    def get_all_tasks(self):
        tasks_list = requests.get(
            "https://beta.todoist.com/API/v8/tasks",
            headers={
                "Authorization": "Bearer %s" % self.api_token
            }).json()
        return tasks_list

    def get_today_tasks(self):
        all_tasks = self.get_all_tasks()
        today_tasks = []

        today = datetime.today().date()
        for task in all_tasks:
            task_due = task.get('due')
            if task_due:
                task_due_date_string = task_due.get('date')
                task_due_date = datetime.strptime(task_due_date_string, '%Y-%m-%d').date()
                if task_due_date == today:
                    today_tasks.append(task)

        return today_tasks

    def create_task(self, task_content):
        result = requests.post(
            "https://beta.todoist.com/API/v8/tasks",
            data=json.dumps({
                "content": task_content,
            }),
            headers={
                "Content-Type": "application/json",
                "X-Request-Id": str(uuid.uuid4()),
                "Authorization": "Bearer %s" % self.api_token
            }).json()

        return result
