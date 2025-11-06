import os
import re
import time
import base64
import logging
from typing import Dict, List, Any
from openai import OpenAI

# -------------------------------------------------------------------
# Logging setup
# -------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# OpenAI Client
# -------------------------------------------------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------------------------------------------------
# Prompt template
# -------------------------------------------------------------------
PROMPT_TEMPLATE = """
You are a local UI automation reasoning agent that observes a live webpage
and decides the correct next interaction.

Goal:
{goal}

You are given BOTH:
1️⃣ A screenshot of the current browser page located at: {image_path}
2️⃣ The visible DOM text (below)

DOM text (trimmed):
{dom_text}

----------------------------------------------------------
Reasoning Guidelines:
----------------------------------------------------------
- Carefully analyze both the screenshot (see {image_path}) and the DOM text.
- Identify visible UI elements: buttons, modals, inputs, dropdowns, etc.
- If a modal or dialog like "New project" or "Create project" is open:
  • Examine whether mandatory fields (e.g., "Project name", "Labels", "Members") are empty.
  • Type short, realistic placeholder text like "AI Test Project" or "Sample Label".
- Titles such as "All issues", "New view", or "Untitled" are often editable <div contenteditable="true"> elements,
  not real inputs. Click the title once, then use action=type to rename it.
- When a field has no label/placeholder/name (nameless contenteditable), set `target` to the **exact visible text**
  currently inside that field (e.g., "All issues", "New view"). Do not add directions or qualifiers.
- Do NOT click "Create", "Save", or "Submit" until required fields are filled.
- If you detect the same screen again with no progress, avoid repeating the same click—fill the required field first.
- If everything appears completed and confirmed, choose action=done.
- If the interface is loading, choose action=wait.
- Always move one logical step closer to the goal, avoiding redundant clicks.

----------------------------------------------------------
Output format (STRICT):
Return ONLY these 4 lines (no markdown, no explanations, no locations). 
For `target`, output **only** the literal UI text of the element (e.g., "All issues"), with no extra words.

- action: [click/type/wait/done]
- target: [exact visible element text; no extra words]
- value: [if typing, the text to type; otherwise blank]
- reasoning: [short one-line reason]
"""

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def _parse_response(text: str) -> Dict[str, str]:
    """Extract structured fields from the model's 4-line response."""
    txt = text.strip()

    def grab(field: str) -> str:
        match = re.search(rf"{field}:\s*(.*)", txt, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    return {
        "action": grab("action").lower(),
        "target": grab("target"),
        "value": grab("value"),
        "reasoning": grab("reasoning"),
        "raw": txt,
    }


def _sanitize_fields(parsed: Dict[str, str]) -> Dict[str, str]:
    """Ensure target/action are clean and usable."""
    t = (parsed.get("target") or "").strip()

    # Cut off accidental descriptive suffixes
    for sep in [" (", " - ", " — ", " -> ", " → ", " under ", " / "]:
        if sep in t:
            t = t.split(sep, 1)[0].strip()

    # Remove quotes, arrows, etc.
    t = t.strip(" '\"").strip()
    parsed["target"] = t
    parsed["action"] = (parsed.get("action") or "").strip().lower()

    return parsed


def _file_to_data_url(path: str) -> str:
    """Read a local image and return a data URL string."""
    ext = os.path.splitext(path)[1].lower().lstrip(".") or "png"
    mime = f"image/{'jpeg' if ext in ('jpg', 'jpeg') else ext}"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def _build_user_content(prompt: str, image_path: str) -> List[Dict[str, Any]]:
    """Build multimodal content payload for GPT-5."""
    content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
    if image_path and os.path.exists(image_path):
        try:
            data_url = _file_to_data_url(image_path)
            content.append({
                "type": "image_url",
                "image_url": {"url": data_url}
            })
        except Exception as e:
            logger.warning("Could not attach image (%s). Continuing text-only. Error: %s", image_path, e)
    return content


def _call_with_retry(create_fn, max_retries: int = 3, base_delay: float = 1.0):
    """Retry wrapper for transient API errors."""
    for attempt in range(max_retries):
        try:
            return create_fn()
        except Exception as e:
            msg = str(e)
            if "429" in msg or "rate" in msg.lower() or "temporarily unavailable" in msg.lower():
                wait = base_delay * (2 ** attempt)
                logger.info("Rate limit hit. Retrying in %.1fs ...", wait)
                time.sleep(wait)
                continue
            raise
    return create_fn()


# -------------------------------------------------------------------
# Main reasoning function
# -------------------------------------------------------------------
def decide_next_action(dom_text: str, goal: str, image_path: str) -> Dict[str, str]:
    """
    Decide the next UI step using GPT-5 reasoning.
    Takes in DOM text + screenshot path for multimodal reasoning.
    """
    dom_excerpt = (dom_text or "")[:6000]
    prompt = PROMPT_TEMPLATE.format(goal=goal, dom_text=dom_excerpt, image_path=image_path)

    logger.info("🧠 Calling GPT-5 with context for goal '%s'...", goal)

    try:
        user_content = _build_user_content(prompt, image_path)

        response = _call_with_retry(
            lambda: client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "You are a precise UI reasoning agent that outputs structured commands for automation."},
                    {"role": "user", "content": user_content},
                ],
                #temperature=0.2,
            )
        )

        raw_output = response.choices[0].message.content.strip()
        logger.info("Model raw output:\n%s", raw_output)

    except Exception as e:
        logger.error("❌ OpenAI API call failed: %s", e)
        return {
            "action": "wait",
            "target": "",
            "value": "",
            "reasoning": "API error — waiting for next step.",
            "raw": str(e),
        }

    parsed = _parse_response(raw_output)
    parsed = _sanitize_fields(parsed)
    logger.info("✅ Parsed action: %s", parsed)
    return parsed


# -------------------------------------------------------------------
# Self-test (optional)
# -------------------------------------------------------------------
if __name__ == "__main__":
    out = decide_next_action(
        dom_text="Editable title: All issues | Button: Save | Input: Description",
        goal="Rename the view to 'sample-view' in Linear",
        image_path="screenshots/step_0.png"
    )
    print(out)
