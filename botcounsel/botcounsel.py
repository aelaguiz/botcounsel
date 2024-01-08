from . import model

def init(openai_model_name, openai_api_key, temp=0.5):
    model.init(openai_model_name, openai_api_key, None, None, temp=temp)