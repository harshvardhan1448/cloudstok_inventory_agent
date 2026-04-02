import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
load_dotenv()

from agent.agent import build_agent

agent = build_agent()
result = agent.invoke({"input": "Check stock for Power Supply 220V"})
print(result["output"])
