from langchain.memory import ConversationBufferMemory

class Expert:
    def __init__(self, name, title, mandate, base_chat_memory):
        self.name = name
        self.title = title
        self.mandate = mandate
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

class CommunicatorExpert(Expert):
    pass

class ModeratorExpert(Expert):
    pass