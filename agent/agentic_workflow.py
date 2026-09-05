
from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from prompt_library.prompt import SYSTEM_PROMPT
from utils.model_loader import ModelLoader
from tools.weather_info_tool import WeatherInfoTool
from tools.place_search_tool import PlaceSearchTool
from tools.expense_calculator_tool import CalculatorTool
from tools.currency_conversion_tools import CurrencyConverterTool

class GraphBuilder:
    def __init__(self, model_provider: str = "groq", llm=None, tools=None, max_steps: int = 24):
        self.model_loader = None if llm is not None else ModelLoader(model_provider=model_provider)
        self.llm = llm or self.model_loader.load_llm()
        self.max_steps = max_steps
        self.tools = list(tools) if tools is not None else self._load_tools()
        self.llm_with_tools = self.llm.bind_tools(tools=self.tools)
        self.graph = None
        self.system_prompt = SYSTEM_PROMPT

    @staticmethod
    def _load_tools():
        weather_tools = WeatherInfoTool()
        place_search_tools = PlaceSearchTool()
        calculator_tools = CalculatorTool()
        currency_converter_tools = CurrencyConverterTool()
        return [
            *weather_tools.weather_tool_list,
            *place_search_tools.place_search_tool_list,
            *calculator_tools.calculator_tool_list,
            *currency_converter_tools.currency_converter_tool_list,
        ]

    def agent_function(self, state: MessagesState):
        """Main agent function"""
        response = self.llm_with_tools.invoke([self.system_prompt, *state["messages"]])
        return {"messages": [response]}

    def build_graph(self):
        if self.graph is not None:
            return self.graph
        graph_builder = StateGraph(MessagesState)
        graph_builder.add_node("agent", self.agent_function)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_edge(START, "agent")
        graph_builder.add_conditional_edges("agent",tools_condition)
        graph_builder.add_edge("tools", "agent")
        self.graph = graph_builder.compile()
        return self.graph

    def invoke(self, question: str):
        """Run one bounded request through the compiled graph."""

        return self.build_graph().invoke(
            {"messages": [HumanMessage(content=question)]},
            config={"recursion_limit": self.max_steps},
        )

    def __call__(self):
        return self.build_graph()