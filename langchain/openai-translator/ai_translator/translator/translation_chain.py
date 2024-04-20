from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.schema.messages import AIMessage
from langchain_community.llms.chatglm3 import ChatGLM3
from langchain_community.llms import ChatGLM
from langchain_core.prompts import PromptTemplate

from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from utils import LOG

# support models
# chatglm3-6b
# chatglm2-6b
# gpt-*
class TranslationChain:
    def __init__(self, model_name: str = "gpt-3.5-turbo", verbose: bool = True):
        
        # 翻译任务指令始终由 System 角色承担
        template = (
            """You are a translation expert, proficient in various languages. \n
            Translates {source_language} to {target_language}."""
        )
        system_message_prompt = SystemMessagePromptTemplate.from_template(template)

        # 待翻译文本由 Human 角色输入
        human_template = "{text}"
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        # 使用 System 和 Human 角色的提示模板构造 ChatPromptTemplate
        chat_prompt_template = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )
        
        if model_name.startswith("gpt"):
            # 为了翻译结果的稳定性，将 temperature 设置为 0
            chat = ChatOpenAI(model_name=model_name, temperature=0, verbose=verbose)

            self.chain = LLMChain(llm=chat, prompt=chat_prompt_template, verbose=verbose)
        elif model_name == "chatglm3-6B":
            
            endpoint_url = "http://127.0.0.1:8000/v1/chat/completions"
            llm = ChatGLM3(
                endpoint_url=endpoint_url,
                max_tokens=80000,
                # prefix_messages=messages,
                # top_p=0.9,
                temperature=0
            )
            self.chain = LLMChain(llm=llm, prompt=chat_prompt_template, verbose=verbose)
        elif model_name == "chatglm2-6B":
            endpoint_url = "http://127.0.0.1:8001"
            llm = ChatGLM(
                endpoint_url=endpoint_url,
                max_token=80000,
                # top_p=0.9,
                temperature=0,
                model_kwargs={"sample_model_args": False},
            )
            self.chain = LLMChain(llm=llm, prompt=chat_prompt_template, verbose=verbose)
        else:
            LOG.error(f"Unsupported model: {model_name}")

    def run(self, text: str, source_language: str, target_language: str) -> (str, bool):
        result = ""
        try:
            result = self.chain.run({
                "text": text,
                "source_language": source_language,
                "target_language": target_language,
            })
        except Exception as e:
            LOG.error(f"An error occurred during translation: {e}")
            return result, False

        return result, True