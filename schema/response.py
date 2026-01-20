import re
import json
def parse_llm_json(text: str) -> dict:
    text = text.strip()

    # 去掉 markdown
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    # 尝试只截取第一个 {...}
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON object found in LLM output")

    json_str = text[start:end+1]
    return json.loads(json_str)

def user_xml(string):##给用户输入加上xml标签
    return '<user_input>'+str(string)+'</user_input>'
def log_xml(string):
    return '<log draft>'+str(string)+'</log draft>'
def previous_xml(string):
    return '<previous chats>'+str(string)+'</previous chats>'
def log_data_xml(string):
    return '<log data>'+'这是用户一部分的历史日志数据：'+str(string)+'</log data>'
def file_list_xml(string):
    return '<file list>'+str(string)+'</file list>'
def user_profile_xml(string):
    return '<user profile>'+str(string)+'</user profile>'
def context_to_text(context: list[dict]) -> str:
    return "\n".join(
        f"{item['role']}: {item['content']}"
        for item in context
    )
