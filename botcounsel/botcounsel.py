from . import model

def init(openai_model_name, openai_api_key, db_connection_string, record_manager_connection_string, temp=0.5):
    model.init(openai_model_name, openai_api_key, db_connection_string, record_manager_connection_string, temp=temp)