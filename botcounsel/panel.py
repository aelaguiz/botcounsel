import logging
logger = logging.getLogger(__name__)

from .model import get_llm
from .prompts import expert_greeting_prompt, communicator_greeting_prompt, moderator_greeting_prompt, moderator_expert_introduction_prompt
from langchain.memory import ConversationBufferMemory
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate

class ExpertPanelManager:
    def __init__(self):
        self.chat_history = ConversationBufferMemory(input_key="input", output_key="output", return_messages=True)
        self.panelists = []

    def set_moderator(self, moderator):
        self.moderator = moderator
        
    def set_communicator(self, communicator):
        self.communicator = communicator
        
    def add_panelist(self, panelist):
        self.panelists.append(panelist)

    def start_panel(self, panel_name, panel_description, panel_goals):
        self.panel_name = panel_name
        self.panel_description = panel_description
        self.panel_goals = panel_goals

        self.welcome_panelists()

        
    def welcome_panelists(self):
        """
        Explains the panel to each of the experts
        """

        llm = get_llm()
        prompt = SystemMessagePromptTemplate.from_template(expert_greeting_prompt)

        for panelist in self.panelists:
            intro_info = {
                'expert_name': panelist.name,
                'expert_title': panelist.title,
                'expert_role': panelist.mandate,
                'panel_name': self.panel_name,
                'panel_description': self.panel_description,
                'panel_goals': self.panel_goals
            }
            fmted_prompt = prompt.format(**intro_info)
            logger.debug(fmted_prompt.content)

            # This assumes that the panelist has a work_memory attribute that is a ConversationBufferMemory object
            panelist.work_memory.chat_memory.add_message(fmted_prompt)

        
        communicator_prompt = SystemMessagePromptTemplate.from_template(communicator_greeting_prompt)

        fmted_prompt = communicator_prompt.format(**{
            'expert_name': self.communicator.name,
            'expert_title': self.communicator.title,
            'expert_role': self.communicator.mandate,
            'panel_name': self.panel_name,
            'panel_description': self.panel_description,
            'panel_goals': self.panel_goals
        })
        logger.debug(fmted_prompt.content)

        # This assumes that the panelist has a work_memory attribute that is a ConversationBufferMemory object
        self.communicator.work_memory.chat_memory.add_message(fmted_prompt)

        moderator_prompt = SystemMessagePromptTemplate.from_template(moderator_greeting_prompt)

        fmted_prompt = moderator_prompt.format(**{
            'expert_name': self.moderator.name,
            'expert_title': self.moderator.title,
            'expert_role': self.moderator.mandate,
            'panel_name': self.panel_name,
            'panel_description': self.panel_description,
            'panel_goals': self.panel_goals
        })
        logger.debug(fmted_prompt.content)

        # This assumes that the panelist has a work_memory attribute that is a ConversationBufferMemory object
        self.moderator.work_memory.chat_memory.add_message(fmted_prompt)

        moderator_expert_prompt = SystemMessagePromptTemplate.from_template(moderator_expert_introduction_prompt)

        for panelist in self.panelists:
            fmted_prompt = moderator_expert_prompt.format(**{
                'moderator_name': self.moderator.name,
                'expert_name': panelist.name,
                'expert_title': panelist.title,
                'expert_role': panelist.mandate,
                'panel_name': self.panel_name,
                'panel_description': self.panel_description,
                'panel_goals': self.panel_goals
            })
            logger.debug(fmted_prompt.content)

            # This assumes that the panelist has a work_memory attribute that is a ConversationBufferMemory object
            self.moderator.work_memory.chat_memory.add_message(fmted_prompt)


    def ask_panel(self, user_input):
        """
        1. Communicator translates the user input focusing on clarity and goals
        2. Moderator clearly defines the problem statement for the other expert, breaking it down for each expert.
        3. Reseracher takes the problem statement and past context and retrieves relevent materials
        4. All experts in parallel receive the guidance from the moderator, the research from the researcher, the chat history and reference their own work history. They produce a report. In a report they present questions that need to be clarified, ideas they are currently exploring, and conclusions they have reached
        5. Moderator reviews reports from the experts, the research from the researcher and decides what to go back to the user with. They can go back with clarifying questions, or they can go back with conclusions, or they can go back with a blend of tentative conclusions as well as questions that need clarification.
        6. Commentator takes the moderator's output and translates it into something that is suitable for direct communication with the user, this is where any tone/style is applied.
        """

        logger.debug(f"User input: {user_input}")

        communicator_output = self.communicator.process_input(user_input)

        logger.debug(f"Communicator output: {communicator_output}")