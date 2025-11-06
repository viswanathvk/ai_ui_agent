from playwright.sync_api import sync_playwright
import os
import time
from reasoning import decide_next_action


class BrowserAgent:
    def __init__(self, app_url, screenshot_dir="screenshots"):
        self.app_url = app_url
        self.screenshot_dir = screenshot_dir
        os.makedirs(screenshot_dir, exist_ok=True)

    def run(self, reasoning_func, goal):
        """
        reasoning_func(dom_text, goal, image_path) -> dict(action, target, value, reasoning)
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)

            # Choose session file based on app type
            if "linear.app" in self.app_url:
                storage_path = "linear_state.json"
            elif "notion.so" in self.app_url:
                storage_path = "notion_state.json"
            else:
                storage_path = "state.json"

            # Load or create context
            if os.path.exists(storage_path):
                print(f"🔑 Using saved session: {storage_path}")
                context = browser.new_context(storage_state=storage_path)
            else:
                print(f"🆕 No session found for {self.app_url}. Please log in manually.")
                context = browser.new_context()

            page = context.new_page()
            page.goto(self.app_url, wait_until="domcontentloaded")
            print(f"🌐 Navigated to {self.app_url}")

            step = 0
            last_action, last_target = None, None

            while True:
                # Take screenshot
                img_path = os.path.join(self.screenshot_dir, f"step_{step}.png")
                page.screenshot(path=img_path, full_page=False)

                # Capture DOM text
                try:
                    dom_text = page.inner_text("body")[:8000]
                except Exception:
                    dom_text = ""

                # Feedback for previous click
                if last_action == "click" and last_target:
                    dom_text += f"\n(Note: '{last_target}' was just clicked. If it opened an input field, you can now type.)"

                # Reasoning call
                result = reasoning_func(dom_text, goal, img_path)
                print(
                    f"\n🧠 Step {step} decision:\n"
                    f"action={result.get('action')}, target={result.get('target')}, value={result.get('value')}\n"
                    f"reason={result.get('reasoning')}\n"
                )

                action = (result.get("action") or "").lower()
                target = (result.get("target") or "").strip()
                value = (result.get("value") or "").strip()

                if action == "done":
                    print("✅ Task complete.")
                    break

                try:
                    # -------------------------------------------------
                    # 1️⃣ CLICK ACTION
                    # -------------------------------------------------
                    if action == "click" and target:
                        found_element = False
                        for method in [
                            lambda: page.get_by_text(target, exact=False).click(timeout=4000),
                            lambda: page.get_by_placeholder(target).click(timeout=4000),
                            lambda: page.get_by_label(target, exact=False).click(timeout=4000),
                        ]:
                            try:
                                method()
                                found_element = True
                                break
                            except Exception:
                                continue

                        if not found_element:
                            buttons = page.locator("button, [role='button'], a")
                            for i in range(min(buttons.count(), 40)):
                                try:
                                    label = buttons.nth(i).inner_text(timeout=1000).strip()
                                    if target.lower() in label.lower():
                                        buttons.nth(i).click(timeout=4000)
                                        found_element = True
                                        break
                                except Exception:
                                    continue

                        if found_element:
                            print(f"🖱️ Clicked '{target}' successfully.")
                            last_action, last_target = "click", target
                        else:
                            print(f"⚠️ Could not click '{target}' — element not found.")

                    # -------------------------------------------------
                    # 2️⃣ TYPE ACTION (handles nameless contenteditable)
                    # -------------------------------------------------
                    elif action == "type":
                        filled = False

                        # Try normal input/textarea
                        for method in [
                            lambda: page.get_by_placeholder(target).fill(value, timeout=4000),
                            lambda: page.get_by_label(target, exact=False).fill(value, timeout=4000),
                            lambda: page.fill(f"input[name='{target}']", value, timeout=4000),
                            lambda: page.fill(f"textarea[name='{target}']", value, timeout=4000),
                        ]:
                            try:
                                method()
                                filled = True
                                break
                            except Exception:
                                continue

                        # Handle <div contenteditable="true">
                        if not filled:
                            try:
                                editable = page.locator("[contenteditable='true']").first
                                editable.click(timeout=4000)
                                try:
                                    page.keyboard.press("Meta+A")
                                except Exception:
                                    page.keyboard.press("Control+A")
                                page.keyboard.type(value, delay=20)
                                filled = True
                            except Exception:
                                pass

                        # Fallback: click near visible target text
                        if not filled and target:
                            try:
                                near = page.get_by_text(target, exact=False).first
                                near.click(timeout=3000)
                                page.keyboard.type(value, delay=20)
                                filled = True
                            except Exception:
                                pass

                        if filled:
                            print(f"✏️ Typed '{value}' successfully.")
                            last_action, last_target = None, None
                        else:
                            print(f"⚠️ Could not fill '{target}' — field not found.")
                            try:
                                editable_fields = page.locator("[contenteditable='true']").all_inner_texts()
                                print("🧩 Visible contenteditable fields:\n", editable_fields)
                            except Exception:
                                pass

                    else:
                        # WAIT or undefined
                        time.sleep(2)

                except Exception as e:
                    print(f"⚠️ Action error: {e}")

                step += 1
                time.sleep(1.5)

            # Save updated session
            context.storage_state(path=storage_path)
            print(f"💾 Session updated: {storage_path}")

            browser.close()
