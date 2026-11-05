"""Agenten-Schleife: das LLM wählt Tools, der Code führt sie geprüft aus."""
import anthropic
from dotenv import load_dotenv

from tools import TOOL_SCHEMAS, execute_tool

load_dotenv()
client = anthropic.Anthropic()

MODEL = "claude-haiku-5-5"
MAX_STEPS = 5


def run_agent(user: str, question: str) -> str:
    """Beantwortet eine Frage mit höchstens MAX_STEPS LLM-Aufrufen.
    Der System-Prompt ist nur Kontext, die Sicherheit liegt in execute_tool.
    """
    system = (
        "Du bist ein Depot-Assistent einer Vermögensverwaltung. "
        f"Angemeldeter Nutzer: {user}. "
        "Nutze die Tools, um Fragen zu Fonds und Depots zu beantworten. "
        "Antworte knapp auf Deutsch, Beträge in Euro."
    )
    messages = [{"role": "user", "content": question}]

    for step in range(1, MAX_STEPS + 1):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")

        results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"-> [Step {step}/{MAX_STEPS}] Agent calls {block.name}({block.input})")
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": execute_tool(user, block.name, block.input),
                })
        messages.append({"role": "user", "content": results})

    return f"Stopped after {MAX_STEPS} steps."
