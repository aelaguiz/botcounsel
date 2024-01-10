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


logger = logging.getLogger(__name__)

from test_panels import nerd_panel
import botcounsel
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.indexes import SQLRecordManager, index


openai_api_key = os.getenv('OPENAI_API_KEY')
openai_model = os.getenv('OPENAI_MODEL_NAME')
openai_temp = float(os.getenv('OPENAI_TEMPERATURE'))
db_connection_string = os.getenv('DB_CONNECTION_STRING')
record_manager_connection_string = os.getenv('RECORDMANAGER_CONNECTION_STRING')

botcounsel.botcounsel_init(openai_model, openai_api_key, db_connection_string, record_manager_connection_string, temp=openai_temp)

from datasets import load_dataset

def find_keyword_matches(dataset, keyword, max_results):
    """
    Search for documents in a dataset that contain a given keyword.

    :param dataset: The dataset to search through.
    :param keyword: The keyword to search for.
    :param max_results: The maximum number of matching documents to return.
    :return: A list of up to max_results documents that contain the keyword.
    """
    keyword = keyword.lower()  # Convert keyword to lowercase for case-insensitive search
    matches = []

    for item in dataset:
        # Assuming the text to search is in item['text']
        if keyword in item['text'].lower():
            matches.append(item)
            if len(matches) >= max_results:
                break

    return matches


res = load_dataset("wikipedia", "20220301.en")

short_list = find_keyword_matches(res['train'], "science fiction", 1000)

docs = [Document(page_content=w['text'], metadata={
    'id': w['id'],
    'url': w['url'],
    'title': w['title'],
    'source': 'wikipedia'
}) for w in short_list]

logger.info(f"Created {len(docs)} documents")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=5000,
    chunk_overlap=200,
    add_start_index=True
)

split_docs = text_splitter.split_documents(docs)
logging.info(f"Splitted {len(split_docs)} documents")

vectordb = botcounsel._get_vectordb()
record_manager = botcounsel._get_record_manager()

logging.info(f"Indexing {len(split_docs)} documents")

res = index(
    docs,
    record_manager,
    vectordb,
    cleanup=None,
    source_id_key="source"
)

logging.info("Done indexing")