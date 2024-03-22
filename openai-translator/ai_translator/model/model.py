from book import ContentType

class Model:
    def make_text_prompt(self, text: str, target_language: str) -> str:
        return f"翻译为{target_language}：{text}"

    def make_table_prompt(self, table: str, target_language: str) -> str:
        return f"翻译为{target_language}，保持间距（空格，分隔符），以表格形式返回：\n{table}"
        # return f"将输入中的文本翻译为{target_language}，输出格式与输入格式保持不变，保留所有非文本字符（包括空格、换行符等），仅用翻译后的文本替换输入中的原始文本进行返回，确保行与行之间有换行符，并且文本带有引号，避免用python解析时出错：\n{table}"

#         return f"""请帮我翻译以下文本内容，并确保格式和内容与原文保持一致。翻译结果需要以空格分隔的文本行形式呈现，每行代表表格的一行数据，第一行是列名。翻译后的文本将被用于创建pandas DataFrame。  
  
# 原文内容如下：  
# {table}
  
# 翻译要求：   
# 1. 翻译后的文本格式需与原文保持一致，即每行包含相同数量的字段，字段之间用空格分隔。  
# 2. 请勿添加任何额外的注释或说明文字，只保留翻译后的表格数据。  
  
# 翻译后的文本将用于以下Python代码段中创建DataFrame：  
  
# ```python  
# table_data = [row.strip().split() for row in translation.strip().split('\n')]  
# LOG.debug(table_data)  
# translated_df = pd.DataFrame(table_data[1:], columns=table_data[0])
# ```
# """  

    def translate_prompt(self, content, target_language: str) -> str:
        if content.content_type == ContentType.TEXT:
            return self.make_text_prompt(content.original, target_language)
        elif content.content_type == ContentType.TABLE:
            return self.make_table_prompt(content.get_original_as_str(), target_language)

    def make_request(self, prompt):
        raise NotImplementedError("子类必须实现 make_request 方法")
