import logging

from langchain.memory import ConversationBufferMemory
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from .model import get_llm, get_vectordb
from langchain_core.output_parsers import StrOutputParser
from .lc_logger import LlmDebugHandler
from .prompts import moderator_outbound_expert_prompt, expert_greeting_prompt, moderator_greeting_inbound_prompt, moderator_expert_introduction_prompt, moderator_panelist_response_intro_prompt, moderator_panelist_response_prompt
from langchain.agents import AgentExecutor

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.tools.retriever import create_retriever_tool
from langchain.agents import OpenAIFunctionsAgent

logger = logging.getLogger(__name__)


lmd = LlmDebugHandler()

class Expert:
    def __init__(self, name, title, expertise, mandate, base_chat_memory):
        self.name = name
        self.title = title
        self.expertise = expertise
        self.mandate = mandate
        self.panel_instructions = []
        self.base_chat_memory = base_chat_memory  # Shared BaseChatMemory object for chat history
        self.message_history = ChatMessageHistory()

        self.llm = get_llm()
        self.vector_db = get_vectordb()
        self.retriever = self.vector_db.as_retriever()

        self.retriever_tool = create_retriever_tool(
            self.retriever,
            "wikipedia_search",
            "Search through wikipedia articles",
        )
        self.tools = [self.retriever_tool]

    def welcome(self, panel_name, panel_description, panel_goals):
        self.panel_name = panel_name
        self.panel_description = panel_description
        self.panel_goals = panel_goals

        self.agent_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(expert_greeting_prompt), 
            MessagesPlaceholder(variable_name='chat_history'),
            HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=['input'], template='{input}')),
            MessagesPlaceholder(variable_name='agent_scratchpad')
        ])

        self.agent = OpenAIFunctionsAgent(
            llm=self.llm,
            prompt=self.agent_prompt,
            tools=self.tools
        )
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, callbacks=[lmd])

        self.agent_with_chat_history = RunnableWithMessageHistory(
            self.agent_executor,
            # This is needed because in most real world scenarios, a session id is needed
            # It isn't really used here because we are using a simple in memory ChatMessageHistory
            lambda session_id: self.message_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )


    def prompt_expert(self, expert_input):
        logger.debug(f"Prompting expert {self.name} - {self.title}: {expert_input}")
        res = self.agent_with_chat_history.invoke(
            {
                "input": expert_input,
                'expert_name': self.name,
                'expert_title': self.title,
                'expert_expertise': self.expertise,
                'expert_mandate': self.mandate,
                'panel_name': self.panel_name,
                'panel_description': self.panel_description,
                'panel_goals': self.panel_goals
            },
            config={"configurable": {"session_id": "<foo>", 'callbacks': [lmd]}}
        )
        output = res['output']
        logger.debug(f"Expert {self.name} - {self.title} response: {output}")
        return output


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

        user_prompt = SystemMessagePromptTemplate.from_template("User said: {user_input}")
        fmted_user_prompt = user_prompt.format(**{
            'user_input': user_input
        })
        llm = get_llm()

        prompts = self.inbound_panel_instructions + [ fmted_user_prompt ]

        res = llm.invoke(
            prompts
        )
        logger.debug(res.content)

        # if not self.message_history.messages:
        #     for p in self.inbound_panel_instructions:
        #         self.message_history.add_message(p)

        self.message_history.add_message(fmted_user_prompt)

        return res.content

    def process_output(self, moderator_output):
        logger.debug(f"Communicator received moderator output: {moderator_output}")

        user_prompt = SystemMessagePromptTemplate.from_template("{moderator_output}")
        fmted_user_prompt = user_prompt.format(**{
            'moderator_output': moderator_output
        })
        llm = get_llm()

        prompts = [m for m in self.message_history.messages] + self.outbound_panel_instructions + [ fmted_user_prompt ]

        print("MESSAGE HISTORY MESSAGES")
        for m in self.message_history.messages:
            print("\n\n------------------------------")
            print(m)
            print(type(m))

        print("COMBINED PROMPTS")
        for p in prompts:
            print("\n\n------------------------------")
            print(p)
        # for p in self.message_history.messages:
        #     logger.debug(p)
        print(type(self.message_history.messages))
        # print(type(self.outbound_panel_instructions))
        # print(self.message_history.messages)
        # print(self.outbound_panel_instructions)
        print(prompts)

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

    def welcome(self, panel_name, panel_description, panel_goals, communicator_name, communicator_title, communicator_expertise, communicator_mandate):
        self.panel_name = panel_name
        self.panel_description = panel_description
        self.panel_goals = panel_goals
        self.communicator_name = communicator_name
        self.communicator_title = communicator_title
        self.communicator_expertise = communicator_expertise
        self.communicator_mandate = communicator_mandate

        inbound_moderator_prompt = SystemMessagePromptTemplate.from_template(moderator_greeting_inbound_prompt)

        inbound_fmted_prompt = inbound_moderator_prompt.format(**{
            'expert_name': self.name,
            'expert_title': self.title,
            'expert_expertise': self.expertise,
            'expert_mandate': self.mandate,
            'communicator_name': self.communicator_name,
            'communicator_title': self.communicator_title,
            'communicator_expertise': self.communicator_expertise,
            'communicator_mandate': self.communicator_mandate,
            'panel_name': self.panel_name,
            'panel_description': self.panel_description,
            'panel_goals': self.panel_goals
        })
        logger.debug(inbound_fmted_prompt.content)
        # self.message_history.add_message(inbound_fmted_prompt)
        self.inbound_panel_instructions = [inbound_fmted_prompt]

        moderator_expert_prompt = SystemMessagePromptTemplate.from_template(moderator_expert_introduction_prompt)

        for panelist in self.panelists:
            fmted_prompt = moderator_expert_prompt.format(**{
                'moderator_name': self.name,
                'panelist_name': panelist.name,
                'panelist_title': panelist.title,
                'panelist_expertise': panelist.expertise,
                'panelist_mandate': panelist.mandate,
                'panel_name': self.panel_name,
                'panel_description': self.panel_description,
                'panel_goals': self.panel_goals
            })
            logger.debug(fmted_prompt.content)
            # self.message_history.add_message(fmted_prompt)


    def process_input(self, communicator_input):
        logger.debug(f"Moderator received input: {communicator_input}")

        prompts = []
        
        panelist_responses = []
        for panelist in self.panelists:
            panelist_prompt = SystemMessagePromptTemplate.from_template(moderator_outbound_expert_prompt)
            fmted_panelist_prompt = panelist_prompt.format(**{
                'communicator_input': communicator_input,
                'expert_name': panelist.name,
                'expert_title': panelist.title,
                'expert_expertise': panelist.expertise,
                'expert_mandate': panelist.mandate
            })
            panelist_prompts = self.inbound_panel_instructions + [ fmted_panelist_prompt ]
            prompts.append(panelist_prompts)

        llm = get_llm()
        batch_res = llm.batch(
            prompts
        )

        moderator_expert_results_prompt = SystemMessagePromptTemplate.from_template(moderator_panelist_response_intro_prompt)
        fmted_panelist_prompt = moderator_expert_results_prompt.format(**{
            'panel_name': self.panel_name,
            'communicator_input': communicator_input
        })

        panelist_results_prompt = [fmted_panelist_prompt]
        for panelist, res in zip(self.panelists, batch_res):
            moderator_expert_msg = res.content

            logger.debug(f"Moderator's prompt to the expert {panelist.name} - {panelist.title}")
            logger.debug(moderator_expert_msg)

            res = panelist.prompt_expert(moderator_expert_msg)

            logger.debug(f"Moderator received response from expert {panelist.name} - {panelist.title}: {res}")

            moderator_expert_results_prompt = SystemMessagePromptTemplate.from_template(moderator_panelist_response_prompt)
            fmted_panelist_prompt = moderator_expert_results_prompt.format(**{
                'panelist_name': panelist.name,
                'panelist_title': panelist.title,
                'panelist_response': res
            })

            panelist_results_prompt.append(fmted_panelist_prompt)


        # TODO Add in a chat history so the moderator has some context on the communications between the panelists and it,
        # TODO - Add in chat history so the moderato rhas context on communications between it and the communicator

        logger.debug(panelist_results_prompt)

        moderator_res = llm.invoke(
            panelist_results_prompt
        )

        logger.debug(moderator_res.content)

        return moderator_res.content