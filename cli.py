import logging
import logging.config
import dotenv
import os


dotenv.load_dotenv()

# Define the configuration file path based on the environment
config_path = os.getenv('LOGGING_CONF_PATH')

# Use the configuration file appropriate to the environment
logging.config.fileConfig(config_path)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("httpcore.connection").setLevel(logging.CRITICAL)
logging.getLogger("httpcore.http11").setLevel(logging.CRITICAL)
logging.getLogger("openai._base_client").setLevel(logging.CRITICAL)

from test_panels import nerd_panel
import botcounsel

openai_api_key = os.getenv('OPENAI_API_KEY')
openai_model = os.getenv('OPENAI_MODEL_NAME')
openai_temp = float(os.getenv('OPENAI_TEMPERATURE'))
db_connection_string = os.getenv('DB_CONNECTION_STRING')
record_manager_connection_string = os.getenv('RECORDMANAGER_CONNECTION_STRING')

botcounsel.botcounsel_init(openai_model, openai_api_key, db_connection_string, record_manager_connection_string, temp=openai_temp)


# communicator = expert.Expert("Adam Savage", chat_history)
# moderator = expert.ModeratorExpert("Ira Flatow", chat_history)

panel = botcounsel.ExpertPanelManager()
communicator = botcounsel.CommunicatorExpert(nerd_panel.panel["communicator"]["name"], nerd_panel.panel["communicator"]["title"], nerd_panel.panel["communicator"]["expertise"], nerd_panel.panel["communicator"]["mandate"], panel.chat_history)
panel.set_communicator(communicator)

moderator = botcounsel.ModeratorExpert(nerd_panel.panel["moderator"]["name"], nerd_panel.panel["moderator"]["title"], nerd_panel.panel["moderator"]["expertise"], nerd_panel.panel["moderator"]["mandate"], panel.chat_history)
panel.set_moderator(moderator)

for panelist_description in nerd_panel.panel["panelists"]:
    panelist = botcounsel.Expert(panelist_description["name"], panelist_description["title"], panelist_description["expertise"], panelist_description["mandate"], panel.chat_history)
    panel.add_panelist(panelist)

user_input = "What specific book written in the 2020s does the panel to be the most impressive? I'm looking for a list of 1-3 specific books."

panel.start_panel(nerd_panel.panel["panel"]["name"], nerd_panel.panel["panel"]["description"], nerd_panel.panel["panel"]["goals"])
panel.ask_panel(user_input)
