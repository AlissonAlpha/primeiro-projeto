from typing import TypedDict, Annotated, Optional, List
from langgraph.graph.message import add_messages


class CopyBrief(TypedDict):
    product: str
    audience: str
    objective: str        # leads, vendas, awareness, trafego
    tone: str             # profissional, descontraido, urgente, inspirador
    differentials: str
    cta: Optional[str]


class AdCopy(TypedDict):
    headline: str          # até 40 chars (Meta)
    primary_text: str      # texto principal do anúncio
    description: str       # descrição curta
    cta_button: str        # LEARN_MORE, SIGN_UP, SHOP_NOW, CONTACT_US, GET_QUOTE
    hook: str              # primeira frase que para o scroll


class CopyAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    brief: Optional[CopyBrief]
    copies: Optional[List[AdCopy]]   # 3 variações
    selected_copy: Optional[AdCopy]
    current_step: str
    error: Optional[str]
