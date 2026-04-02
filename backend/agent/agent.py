import os
import re

from agent.prompts import SYSTEM_PROMPT
from agent.tools import check_stock, generate_report, semantic_search, update_inventory


class FallbackInventoryAgent:
    def invoke(self, payload):
        user_input = payload.get("input", "")
        lowered = user_input.lower()

        if "report" in lowered:
            report_type = "low_stock" if "low" in lowered else "full_summary"
            return {"output": generate_report.invoke(report_type)}

        if any(word in lowered for word in ["compatible", "compatibility", "manual", "spec", "specification"]):
            return {"output": semantic_search.invoke(user_input)}

        if "stock" in lowered or "check" in lowered:
            match = re.search(
                r"(?:check\s+stock(?:\s+for)?|stock(?:\s+for)?|check)(.*)$",
                user_input,
                re.IGNORECASE,
            )
            query = match.group(1).strip() if match and match.group(1).strip() else user_input
            return {"output": check_stock.invoke(query)}

        if any(word in lowered for word in ["add", "remove", "update", "units"]):
            sku_match = re.search(r"SKU-\d+", user_input, re.IGNORECASE)
            qty_match = re.search(r"(-?\d+)\s+units?", user_input, re.IGNORECASE)
            reason_match = re.search(r"reason\s*:\s*(.+)$", user_input, re.IGNORECASE)
            sku = sku_match.group(0).upper() if sku_match else ""
            quantity_change = int(qty_match.group(1)) if qty_match else 0
            if "remove" in lowered and quantity_change > 0:
                quantity_change = -quantity_change
            reason = reason_match.group(1).strip() if reason_match else "manual update"
            return {"output": update_inventory.invoke({"sku": sku, "quantity_change": quantity_change, "reason": reason})}

        return {
            "output": (
                "I can check stock, update inventory, generate reports, or search manuals. "
                "Try asking about a SKU, a report, or product compatibility."
            )
        }


class SafeAgentWrapper:
    def __init__(self, primary_agent, fallback_agent):
        self.primary_agent = primary_agent
        self.fallback_agent = fallback_agent

    def invoke(self, payload):
        user_input = payload.get("input", "")
        lowered = user_input.lower()
        deterministic_intent = any(
            token in lowered
            for token in [
                "report",
                "add",
                "remove",
                "update",
                "units",
                "compatible",
                "compatibility",
                "manual",
                "spec",
                "check stock",
            ]
        )
        if deterministic_intent:
            return self.fallback_agent.invoke(payload)
        try:
            return self.primary_agent.invoke(payload)
        except Exception:
            return self.fallback_agent.invoke(payload)


def build_agent():
    fallback = FallbackInventoryAgent()
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
    os.environ.setdefault("LANGSMITH_TRACING", "false")

    try:
        from langchain_groq import ChatGroq
        from langchain.agents import AgentExecutor, create_openai_tools_agent
        from langchain.memory import ConversationBufferWindowMemory
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

        llm = ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            temperature=0,
            streaming=True,
        )

        tools = [check_stock, update_inventory, generate_report, semantic_search]

        memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=10,
            return_messages=True,
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                MessagesPlaceholder("chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )
        agent = create_openai_tools_agent(llm, tools, prompt)

        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
        )
        return SafeAgentWrapper(executor, fallback)
    except Exception:
        return fallback
