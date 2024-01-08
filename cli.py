import logging
import logging.config
import dotenv
import os


dotenv.load_dotenv()

# Define the configuration file path based on the environment
config_path = os.getenv('LOGGING_CONF_PATH')

# Use the configuration file appropriate to the environment
logging.config.fileConfig(config_path)

from test_panels import nerd_panel
import botcounsel

openai_api_key = os.getenv('OPENAI_API_KEY')
openai_model = os.getenv('OPENAI_MODEL_NAME')
openai_temp = float(os.getenv('OPENAI_TEMPERATURE'))

botcounsel.botcounsel_init(openai_model, openai_api_key, temp=openai_temp)


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

user_input = "What is the most impressive sci-fi book of the 2020s?"

panel.start_panel(nerd_panel.panel["panel"]["name"], nerd_panel.panel["panel"]["description"], nerd_panel.panel["panel"]["goals"])
# panel.ask_panel(user_input)

# import logging
# from src.lib import lib_docdb
# import argparse
# from src.lib import lib_logging
# from prompt_toolkit import prompt
# from prompt_toolkit.key_binding import KeyBindings
# from prompt_toolkit.keys import Keys

# # lib_logging.setup_logging()


# # lib_logging.set_console_logging_level(logging.ERROR)
# # logger = lib_logging.get_logger(logging.ERROR)

# def print_email_doc(page_content, metadata):
#     print(page_content)
#     print(metadata)
#     return
#     # Extracting metadata
#     email_id = metadata.get('email_id', 'N/A')
#     from_address = metadata.get('from_address', 'N/A')
#     subject = metadata.get('subject', 'N/A')
#     thread_id = metadata.get('thread_id', 'N/A')
#     to_address = metadata.get('to_address', 'N/A')

#     # Formatting and printing the email document
#     print("Email Document Details")
#     print("----------------------")
#     print(f"Email ID: {email_id}")
#     print(f"Thread ID: {thread_id}")
#     print(f"Subject: {subject}")
#     print(f"From: {from_address}")
#     print(f"To: {to_address}")
#     print("\nContent:")
#     print("----------------------")
#     print(page_content)


# def process_command(input):
#     db = lib_docdb.get_docdb()

#     print(f"Processing: {input}")

#     docs = db.similarity_search_with_relevance_scores(input, k=50)
#     for doc, score in docs:
#         print(f"Score {score}")
#         print_email_doc(doc.page_content, doc.metadata)

#     # res = chain.invoke(input, config={
#     #     'callbacks': [lmd, oaid]
#     # })

#     # print(f"Result: '{res}'")
#     # print(oaid)


# def main():
#     bindings = KeyBindings()

#     while True:
#         multiline = False

#         while True:
#             try:
#                 if not multiline:
#                     # Single-line input mode
#                     line = prompt('Enter text (""" for multiline, "quit" to exit, Ctrl-D to end): ', key_bindings=bindings)
#                     if line.strip() == '"""':
#                         multiline = True
#                         continue
#                     elif line.strip().lower() == 'quit':
#                         return  # Exit the CLI
#                     else:
#                         process_command(line)
#                         break
#                 else:
#                     # Multiline input mode
#                     line = prompt('... ', multiline=True, key_bindings=bindings)
#                     process_command(line)
#                     multiline = False
#             except EOFError:
#                 return


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description='Run the Gmail pipeline for a specific company.')
#     parser.add_argument('company', choices=['cj', 'fc'], help='Specify the company environment ("cj" or "fc").')
#     args = parser.parse_args()

#     lib_docdb.set_company_environment(args.company.upper())


#     main()