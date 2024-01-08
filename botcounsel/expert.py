import logging

from .prompts import communicator_user_input_prompt
from langchain.memory import ConversationBufferMemory
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from .model import get_llm
from langchain_core.output_parsers import StrOutputParser
from .lc_logger import LlmDebugHandler

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

    def welcome(self, panel_name, panel_description, panel_goals):
        self.panel_name = panel_name
        self.panel_description = panel_description
        self.panel_goals = panel_goals

class CommunicatorExpert(Expert):
    def process_input(self, user_input):
        # Turn the user prompt, chat history and work history and generate a message for the moderator
        logger.debug(f"Communicator received input: {user_input}")

        logger.debug(self.work_memory.chat_memory)

        sys_prompt = SystemMessagePromptTemplate.from_template(communicator_user_input_prompt)
        fmted_sys_prompt = sys_prompt.format(**{
            'expert_name': self.name,
            'panel_name': self.panel_name,
            'panel_goals': self.panel_goals,
            'chat_history': self.base_chat_memory.chat_memory,
            'work_history': self.work_memory.chat_memory
        })

        user_prompt = HumanMessagePromptTemplate.from_template("{user_input}")
        fmted_user_prompt = user_prompt.format(**{
            'user_input': user_input
        })
        llm = get_llm()

        res = llm.invoke(
            self.panel_instructions + 
            [
                fmted_sys_prompt,
                fmted_user_prompt
            ]
        )
        logger.debug(res.content)



        # panelist.work_memory.chat_memory.add_message(fmted_prompt)
        

        # My work memory is my conversation with the moderator
        # Prompt I want to assemble:
        ## Panel isntruction messages
        ## New user input system message
        ### History of conversation with user
        ### History of work with moderator
        ## User input

        return ""

class ModeratorExpert(Expert):
    pass