from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from .state import CopyAgentState
from core.llm import get_claude
import json


SYSTEM_PROMPT = """Você é um copywriter especialista em anúncios de alta conversão para Meta Ads (Facebook/Instagram).
Seu estilo combina os princípios de David Ogilvy, Gary Halbert e Eugene Schwartz.

Quando solicitado a criar copies para anúncios, gere SEMPRE 3 variações com abordagens diferentes:
- Variação 1: Foco na DOR/PROBLEMA do público
- Variação 2: Foco no BENEFÍCIO/TRANSFORMAÇÃO
- Variação 3: Foco em PROVA SOCIAL/URGÊNCIA

Para cada variação, forneça:
- **Hook**: Primeira frase que para o scroll (máx 15 palavras)
- **Headline**: Título do anúncio (máx 40 caracteres)
- **Primary Text**: Texto principal (máx 125 palavras, ideal 3-5 linhas)
- **Description**: Linha de descrição curta (máx 30 caracteres)
- **CTA Button**: LEARN_MORE | SIGN_UP | SHOP_NOW | CONTACT_US | GET_QUOTE | BOOK_TRAVEL

Regras de ouro:
1. Fale com UMA pessoa, não com "vocês"
2. Benefício antes de feature
3. Especificidade gera credibilidade (números, prazos, resultados)
4. Termine sempre com CTA claro
5. Adapte o tom ao objetivo: leads=urgência suave, vendas=prova+escassez, awareness=curiosidade

Responda sempre em português brasileiro.
Ao gerar as copies, formate como JSON válido dentro de ```json``` para facilitar o processamento."""


@tool
def generate_copies(
    product: str,
    audience: str,
    objective: str,
    tone: str,
    differentials: str,
    cta_hint: str = "",
) -> str:
    """Generate 3 ad copy variations for Meta Ads based on the brief."""
    return json.dumps({
        "action": "generate_copies",
        "brief": {
            "product": product,
            "audience": audience,
            "objective": objective,
            "tone": tone,
            "differentials": differentials,
            "cta_hint": cta_hint,
        }
    })


COPY_TOOLS = [generate_copies]


def should_continue(state: CopyAgentState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


def call_model(state: CopyAgentState) -> dict:
    llm = get_claude()
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response], "current_step": "copy_generated"}


def build_copy_agent_graph():
    tool_node = ToolNode(COPY_TOOLS)
    graph = StateGraph(CopyAgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue)
    graph.add_edge("tools", "agent")
    return graph.compile()


copy_agent = build_copy_agent_graph()
