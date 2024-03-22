import gradio as gr
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import ArgumentParser, ConfigLoader, LOG, Language
from model import GLMModel, OpenAIModel
from translator import PDFTranslator


def translate(api_key, model_name, pdf_file_path, file_format, target_language):
    model = OpenAIModel(model=model_name, api_key=api_key)
    # 实例化 PDFTranslator 类，并调用 translate_pdf() 方法
    translator = PDFTranslator(model)
    output_file = translator.translate_pdf(pdf_file_path, file_format, target_language)
    return output_file


with gr.Blocks() as demo:
    gr.Markdown("Translate English PDF book to other languages, such as Chinese.")

    with gr.Tab("Config"):
        api_key = gr.Textbox(label="API_KEY",info="Type your openai_api_key.")
        model_name = gr.Dropdown(
            ["gpt-3.5-turbo"], label="Model Name", info="Select Model Name you want to use."
        )

    with gr.Tab("Translation"):
       
        pdf_file_path=gr.File(label="PDF File", file_count="single", file_types=[".pdf"], show_label=True)
        file_format = gr.Dropdown(
            ["markdown","PDF"], label="Output File Type", info="File type of saved translated file."
        )
        target_language = gr.Dropdown(
            list(Language.__members__.values()), label="Translated Language", info="Target language to translate to."
        )
        output = gr.File(label="translated file", file_count="single", show_label=True)
        st_btn = gr.Button("Start")
            
        
    st_btn.click(fn=translate, inputs=[api_key, model_name, pdf_file_path, file_format, target_language], outputs=output)

demo.launch(server_name="0.0.0.0", server_port=8502)