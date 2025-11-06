🧠 Real-Time UI Capture Agent

This project automates real-time user interface (UI) state capture across live web applications. It’s designed as part of a multi-agent automation system where an AI agent observes, reasons, and acts on web UIs — capturing each step of the workflow for downstream analysis or training data generation.

🚀 Overview

The Real-Time UI Capture Agent:

Navigates live web applications (e.g., Notion, Linear, Jira, etc.)

Identifies UI elements dynamically, even when they lack fixed names or IDs

Captures screenshots of each meaningful UI state in the workflow

Uses a reasoning model to decide the next action (click, type, wait, etc.)

Stores all captured states (DOM + images) for replay, debugging, or model training

🧩 Architecture
├── main.py             # Entry point to run the agent
├── browser.py          # Handles Playwright browser automation
├── reasoning.py        # AI reasoning module to decide next action
├── save_state.py       # Reuses saved login sessions
├── screenshots/        # Folder for captured UI screenshots
└── requirements.txt    # Project dependencies

⚙️ How It Works

Goal Input – The user defines a goal (e.g., “Create a new project in Linear”).

Browser Launch – The system opens the target web app using Playwright.

Reasoning Loop – For each state:

Extracts DOM text and takes a screenshot

Passes data to the reasoning model (local or API)

Executes the model’s chosen action (click/type/etc.)

Capture Output – Each UI step is saved as an image + JSON description.

🧠 Reasoning Model

The reasoning logic can run on:

OpenAI GPT models (e.g., gpt-4-turbo)

Local open-source models via Ollama (e.g., llava, moondream, llama3.2-vision)

Example prompt structure:

- action: [click | type | wait | done]
- target: [element label or placeholder]
- value: [if typing, what text]
- reasoning: [why this step was chosen]

🪄 Setup Instructions
1️⃣ Install dependencies
pip install -r requirements.txt

2️⃣ Save your login sessions
python save_state.py

3️⃣ Run the agent
python main.py

4️⃣ View captured screenshots

All captured steps will appear in the screenshots/ folder.

💡 Example Use Case

Goal: “How do I create a project in Linear?”
The agent will:

Load Linear dashboard

Locate “Create project” button

Fill in fields and submit

Capture screenshots of each step

Stop when success state is detected

🧰 Tech Stack

Python 3.10+

Playwright – browser automation

OpenAI / Ollama – reasoning models

PIL / OpenCV – optional image processing

🧱 Future Enhancements

✅ DOM element detection with visual bounding boxes

✅ Integration with LLaVA or GPT-Vision for UI comprehension

🔜 Action replay & workflow reconstruction

🔜 Fine-tuning dataset for RPA and reasoning models

🧑‍💻 Author

Viswa Kasturi
Building intelligent agents that think and act on live UIs.
