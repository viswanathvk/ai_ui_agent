# main.py
from browser import BrowserAgent
from reasoning import decide_next_action
import os

query = input("I'm Agent A — What's your question?\n")

if "linear" in query.lower():
    app_url = "https://linear.app/"
elif "notion" in query.lower():
    app_url = "https://www.notion.so/"
else:
    app_url = "https://google.com"

folder_name = "screenshots/" + query.replace(" ", "_")
agent = BrowserAgent(app_url, screenshot_dir=folder_name)
agent.run(decide_next_action, query)
