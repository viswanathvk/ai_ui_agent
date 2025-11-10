🧠 Real-Time UI Capture Agent

An AI-powered system that automates real-time UI state capture across web applications using Playwright and reasoning model - GPT 5.

🚀 Features

Navigates web apps (Notion, Linear, etc.)

Detects elements dynamically (even unnamed)

Captures each UI state with screenshots

Uses AI to decide next actions (click, type, wait)

Saves screenshots + reasoning logs for replay

⚙️ Setup
pip install -r requirements.txt
python save_state.py    # Save login session
python main.py          # Run the agent

🧩 Structure

browser.py – handles Playwright
reasoning.py – AI action logic
screenshots/ – captured UI states

👤 Author

Viswa Kasturi 
