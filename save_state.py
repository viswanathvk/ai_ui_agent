from playwright.sync_api import sync_playwright
import os

def save_or_load_session(playwright, site_name, url, state_file):
    print(f"\n==============================")
    print(f"🌐 Processing: {site_name}")
    print(f"==============================")

    browser = playwright.chromium.launch(headless=False)

    # If session already exists, reuse it
    if os.path.exists(state_file):
        print(f"✅ Using existing session for {site_name}")
        context = browser.new_context(storage_state=state_file)
        page = context.new_page()
        page.goto(url)
        print(f"🔓 Already logged into {site_name}.")
        input("Press Enter to continue and close this browser...")
    else:
        print(f"🆕 No saved session for {site_name}. Opening login page...")
        context = browser.new_context()
        page = context.new_page()
        page.goto(url)
        print(f"👉 Please log in manually to {site_name}.")
        print("After you’re fully logged in and the dashboard/workspace loads, press Enter here.")
        input()
        context.storage_state(path=state_file)
        print(f"✅ Login state saved for {site_name} → {state_file}")

    browser.close()


# ---------- MAIN EXECUTION ----------
with sync_playwright() as p:
    save_or_load_session(p, "Linear", "https://linear.app/", "linear_state.json")
    save_or_load_session(p, "Notion", "https://www.notion.so/", "notion_state.json")

print("\n🎉 Both sessions have been processed and saved successfully!")
