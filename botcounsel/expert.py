import logging

from langchain.memory import ConversationBufferMemory
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from .model import get_llm
from langchain_core.output_parsers import StrOutputParser
from .lc_logger import LlmDebugHandler
from .prompts import moderator_outbound_expert_prompt

logger = logging.getLogger(__name__)

class Expert:
    def __init__(self, name, title, expertise, mandate, base_chat_memory):
        self.name = name
        self.title = title
        self.expertise = expertise
        self.mandate = mandate
        self.panel_instructions = []
        self.base_chat_memory = base_chat_memory  # Shared BaseChatMemory object for chat history
        self.work_memory = ConversationBufferMemory(input_key="input", output_key="output", return_messages=True)

    def gather_data(self):
        """
        Gather data .
        This method should be overridden by specific expert implementations.
        """
        raise NotImplementedError("gather_data method not implemented")

    def analyze_data(self):
        """
        Analyze the gathered data.
        This method should be overridden by specific expert implementations.
        """
        raise NotImplementedError("analyze_data method not implemented")

    def prepare_summary(self):
        """
        Prepare a summary based on the analysis.
        This method should be overridden by specific expert implementations.
        """
        raise NotImplementedError("prepare_summary method not implemented")

    def report(self):
        """
        Return the prepared summary.
        """
        if self.summary is None:
            print("No summary available.")
        else:
            return self.summary

    def welcome(self, panel_name, panel_description, panel_goals, panel_instructions=[]):
        self.panel_name = panel_name
        self.panel_description = panel_description
        self.panel_goals = panel_goals
        self.panel_instructions = panel_instructions


class MiddlemanExpert(Expert):
    def welcome(self, panel_name, panel_description, panel_goals, inbound_panel_instructions, outbound_panel_instructions):
        self.panel_name = panel_name
        self.panel_description = panel_description
        self.panel_goals = panel_goals
        self.inbound_panel_instructions = inbound_panel_instructions
        self.outbound_panel_instructions = outbound_panel_instructions

class CommunicatorExpert(MiddlemanExpert):
    def process_input(self, user_input):
        # Turn the user prompt, chat history and work history and generate a message for the moderator
        logger.debug(f"Communicator received input: {user_input}")

        logger.debug(self.work_memory.chat_memory)

        user_prompt = HumanMessagePromptTemplate.from_template("{user_input}")
        fmted_user_prompt = user_prompt.format(**{
            'user_input': user_input
        })
        llm = get_llm()

        prompts = self.inbound_panel_instructions + [ fmted_user_prompt ]

        res = llm.invoke(
            prompts
        )
        logger.debug(res.content)

        return res.content

class ModeratorExpert(MiddlemanExpert):
    def __init__(self, name, title, expertise, mandate, base_chat_memory):
        super().__init__(name, title, expertise, mandate, base_chat_memory)
        self.panelists = []
        
    def add_panelist(self, panelist):
        self.panelists.append(panelist)

    def process_input(self, communicator_input):
        logger.debug(f"Moderator received input: {communicator_input}")

        prompts = []
        
        for panelist in self.panelists:
            panelist_prompt = SystemMessagePromptTemplate.from_template(moderator_outbound_expert_prompt)
            fmted_panelist_prompt = panelist_prompt.format(**{
                'communicator_input': communicator_input,
                'expert_name': panelist.name,
                'expert_title': panelist.title,
                'expert_expertise': panelist.expertise,
                'expert_mandate': panelist.mandate
            })
            panelist_prompts = self.inbound_panel_instructions +  self.panel_instructions + [ fmted_panelist_prompt ]
            prompts.append(panelist_prompts)

        llm = get_llm()
        batch_res = llm.batch(
            prompts
        )

        for panelist, res in zip(self.panelists, batch_res):
            logger.debug(f"Moderator's prompt to the expert {panelist.name} - {panelist.title}")
            logger.debug(res.content)