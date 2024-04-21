"""
一个简单的demo，调用CharacterGLM实现角色扮演，调用CogView生成图片，调用ChatGLM生成CogView所需的prompt。

依赖：
pyjwt
requests
streamlit
zhipuai
python-dotenv

运行方式：
```bash
streamlit run characterglm_api_demo_streamlit.py
```
"""
import os
import itertools
from typing import Iterator, Optional
from logger import LOG

import streamlit as st
from dotenv import load_dotenv
# 通过.env文件设置环境变量
# reference: https://github.com/theskumar/python-dotenv
load_dotenv()

import api
from api import generate_chat_scene_prompt, generate_role_appearance, get_characterglm_response, generate_cogview_image, gen_role
from data_types import TextMsg, ImageMsg, TextMsgList, MsgList, filter_text_msg

st.set_page_config(page_title="CharacterGLM Demo Tool", page_icon="🤖", layout="wide")
debug = os.getenv("DEBUG", "").lower() in ("1", "yes", "y", "true", "t", "on")



def update_api_key(key: Optional[str] = None):
    if debug:
        print(f'update_api_key. st.session_state["API_KEY"] = {st.session_state["API_KEY"]}, key = {key}')
    key = key or st.session_state["API_KEY"]
    if key:
        api.API_KEY = key

# 设置API KEY
api_key = st.sidebar.text_input("API_KEY", value=os.getenv("API_KEY", ""), key="API_KEY", type="password", on_change=update_api_key)
update_api_key(api_key)


# 初始化
if "history" not in st.session_state:
    st.session_state["history"] = []
if "bot1_history" not in st.session_state:
    st.session_state["bot1_history"] = []
if "bot2_history" not in st.session_state:
    st.session_state["bot2_history"] = []
if "meta" not in st.session_state:
    st.session_state["meta"] = {
        "bot2_info": "",
        "bot1_info": "",
        "bot1_name": "",
        "bot2_name": ""
    }


def init_session():
    st.session_state["history"] = []
    st.session_state["bot1_history"] = []
    st.session_state["bot2_history"] = []


# 4个输入框，设置meta的4个字段
meta_labels = {
    "bot1_name": "角色名1",
    "bot2_name": "角色名2", 
    "bot1_info": "角色人设1",
    "bot2_info": "用户人设2"
}

# 2x2 layout
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        st.text_input(label="角色名1", value=st.session_state["meta"]["bot1_name"], key="bot1_name", on_change=lambda : st.session_state["meta"].update(bot1_name=st.session_state["bot1_name"]), help="模型所扮演的角色1的名字，不可以为空")
        st.text_area(label="角色人设1",value=st.session_state["meta"]["bot1_info"], key="bot1_info", on_change=lambda : st.session_state["meta"].update(bot1_info=st.session_state["bot1_info"]), help="角色1的详细人设信息，不可以为空")
        
    with col2:
        st.text_input(label="角色名2", value=st.session_state["meta"]["bot2_name"], key="bot2_name", on_change=lambda : st.session_state["meta"].update(bot2_name=st.session_state["bot2_name"]), help="模型所扮演的角色2的名字，不可以为空")
        st.text_area(label="角色人设2", value=st.session_state["meta"]["bot2_info"], key="bot2_info", on_change=lambda : st.session_state["meta"].update(bot2_info=st.session_state["bot2_info"]), help="角色2的详细人设信息，不可以为空")


def verify_meta() -> bool:
    # 检查`角色名`和`角色人设`是否空，若为空，则弹出提醒
    if st.session_state["meta"]["bot1_name"] == "" or st.session_state["meta"]["bot1_info"] == "" or st.session_state["meta"]["bot2_name"] == "" or st.session_state["meta"]["bot2_info"] == "":
        st.error("角色名和角色人设不能为空")
        return False
    else:
        return True

# def verify_meta() -> bool:
#     # 检查`角色名`和`角色人设`是否空，若为空，则弹出提醒
#     if st.session_state["meta"]["bot_name"] == "" or st.session_state["meta"]["bot_info"] == "":
#         st.error("角色名和角色人设不能为空")
#         return False
#     else:
#         return True


def draw_new_image():
    """生成一张图片，并展示在页面上"""
    if not verify_meta():
        return
    text_messages = filter_text_msg(st.session_state["history"])
    if text_messages:
        # 若有对话历史，则结合角色人设和对话历史生成图片
        image_prompt = "".join(
            generate_chat_scene_prompt(
                text_messages[-10: ],
                meta=st.session_state["meta"]
            )
        )
    else:
        # 若没有对话历史，则根据角色人设生成图片
        image_prompt = "".join(generate_role_appearance(st.session_state["meta"]["bot1_info"]))
    
    if not image_prompt:
        st.error("调用chatglm生成Cogview prompt出错")
        return
    
    # TODO: 加上风格选项
    image_prompt = '二次元风格。' + image_prompt.strip()
    
    print(f"image_prompt = {image_prompt}")
    n_retry = 3
    st.markdown("正在生成图片，请稍等...")
    for i in range(n_retry):
        try:
            img_url = generate_cogview_image(image_prompt)
        except Exception as e:
            if i < n_retry - 1:
                st.error("遇到了一点小问题，重试中...")
            else:
                st.error("又失败啦，点击【生成图片】按钮可再次重试")
                return
        else:
            break
    img_msg = ImageMsg({"role": "image", "image": img_url, "caption": image_prompt})
    # 若history的末尾有图片消息，则替换它，（重新生成）
    # 否则，append（新增）
    while st.session_state["history"] and st.session_state["history"][-1]["role"] == "image":
        st.session_state["history"].pop()
    st.session_state["history"].append(img_msg)
    st.rerun()


button_labels = {
    "create_meta": "生成人设",
    "clear_meta": "清空人设",
    "clear_history": "清空对话历史",
    "gen_picture": "生成图片"
}
if debug:
    button_labels.update({
        "show_api_key": "查看API_KEY",
        "show_meta": "查看meta",
        "show_history": "查看历史"
    })


init_input = st.text_input('请输入一些文本：', '')

# 在同一行排列按钮
with st.container():
    n_button = len(button_labels)
    cols = st.columns(n_button)
    button_key_to_col = dict(zip(button_labels.keys(), cols))

    with button_key_to_col["create_meta"]:
        create_meta = st.button(button_labels["create_meta"], key="create_meta")
        if create_meta:
            # TODO: call glm to create meta
            role_obj = gen_role(init_input)
            st.session_state["meta"] = {
                "bot2_info": role_obj["bot2_info"],
                "bot1_info": role_obj["bot1_info"],
                "bot1_name": role_obj["bot1_name"],
                "bot2_name": role_obj["bot2_name"]
            }
            st.rerun()
    
    with button_key_to_col["clear_meta"]:
        clear_meta = st.button(button_labels["clear_meta"], key="clear_meta")
        if clear_meta:
            st.session_state["meta"] = {
                "user_info": "",
                "bot_info": "",
                "bot_name": "",
                "user_name": ""
            }
            st.rerun()

    with button_key_to_col["clear_history"]:
        clear_history = st.button(button_labels["clear_history"], key="clear_history")
        if clear_history:
            init_session()
            st.rerun()
    
    with button_key_to_col["gen_picture"]:
        gen_picture = st.button(button_labels["gen_picture"], key="gen_picture")
    
    if debug:
        with button_key_to_col["show_api_key"]:
            show_api_key = st.button(button_labels["show_api_key"], key="show_api_key")
            if show_api_key:
                print(f"API_KEY = {api.API_KEY}")
        
        with button_key_to_col["show_meta"]:
            show_meta = st.button(button_labels["show_meta"], key="show_meta")
            if show_meta:
                print(f"meta = {st.session_state['meta']}")
        
        with button_key_to_col["show_history"]:
            show_history = st.button(button_labels["show_history"], key="show_history")
            if show_history:
                print(f"history = {st.session_state['history']}")


# 展示对话历史
for msg in st.session_state["history"]:
    if msg["role"] == "bot1":
        with st.chat_message(name="bot1", avatar="user"):
            st.markdown(msg["content"])
    elif msg["role"] == "bot2":
        with st.chat_message(name="bot2", avatar="assistant"):
            st.markdown(msg["content"])
    elif msg["role"] == "image":
        with st.chat_message(name="assistant", avatar="assistant"):
            st.image(msg["image"], caption=msg.get("caption", None))
    else:
        raise Exception("Invalid role")


if gen_picture:
    draw_new_image()


with st.chat_message(name="bot1", avatar="user"):
    bot1_placeholder = st.empty()
with st.chat_message(name="bot2", avatar="assistant"):
    bot2_placeholder = st.empty()


def output_stream_response(response_stream: Iterator[str], placeholder):
    content = ""
    for content in itertools.accumulate(response_stream):
        placeholder.markdown(content)
    return content

bot1_meta = {
    "user_info": "",
    "bot_info": "",
    "bot_name": "",
    "user_name": ""
}
bot2_meta = {
    "user_info": "",
    "bot_info": "",
    "bot_name": "",
    "user_name": ""
}

def save_chat_history():
    import datetime  
    filename = f"chat_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    with open(filename, 'w') as file: 
        for msg in st.session_state["history"]:
            cur_role = msg["role"]
            key = f"{cur_role}_name"
            role_name = st.session_state["meta"][key]
            content = msg["content"]
            file.write(f"{role_name}: {content}\n")
    return filename
    

def start_chat():

    # 初始化对话列表： bot1 叫 bot2 名字
    init_chat_content = st.session_state["meta"]["bot2_name"]

    gen_chat = st.button("生成对话", key="gen_chat")
    save_chat = st.button("保存对话", key="save_chat")

    if save_chat and st.session_state["history"]:
        filename = save_chat_history()
        if os.path.exists(filename):  
            st.download_button(label="下载文件", data=open(filename, 'rb'), file_name=filename, mime='text')

    if gen_chat:
        if not verify_meta():
            return
        if not api.API_KEY:
            st.error("未设置API_KEY")

        global bot1_meta, bot2_meta
        bot1_meta = {
                "user_info": st.session_state["meta"]["bot1_info"],
                "bot_info": st.session_state["meta"]["bot2_info"],
                "bot_name": st.session_state["meta"]["bot2_name"],
                "user_name": st.session_state["meta"]["bot1_name"]
            }

        bot2_meta = {
                "user_info": st.session_state["meta"]["bot2_info"],
                "bot_info": st.session_state["meta"]["bot1_info"],
                "bot_name": st.session_state["meta"]["bot1_name"],
                "user_name": st.session_state["meta"]["bot2_name"]
            }

        if not st.session_state["history"]:
            bot1_placeholder.markdown(init_chat_content)
            st.session_state["history"].append(TextMsg({"role": "bot1", "content": init_chat_content}))
            st.session_state["bot1_history"].append(TextMsg({"role": "user", "content": init_chat_content}))
            st.session_state["bot2_history"].append(TextMsg({"role": "assistant", "content": init_chat_content}))
            gen_bot1_response()
        else:
            cur_role = st.session_state["history"][-1]["role"]
            LOG.debug(f"current role: {cur_role}")
            if cur_role == "bot2":
                gen_bot2_response()
            elif cur_role == "bot1":
                gen_bot1_response()
            else:
                raise Exception("Invalid role for chat!")


def gen_bot1_response():        
    response_stream = get_characterglm_response(filter_text_msg( st.session_state["bot1_history"]), meta=bot1_meta)
    bot2_response = output_stream_response(response_stream, bot2_placeholder)
    if not bot2_response:
        bot2_placeholder.markdown("生成出错")
        st.session_state["history"].pop()
    else:
        st.session_state["history"].append(TextMsg({"role": "bot2", "content": bot2_response}))
        st.session_state["bot1_history"].append(TextMsg({"role": "assitant", "content": bot2_response}))
        st.session_state["bot2_history"].append(TextMsg({"role": "user", "content": bot2_response}))
    
    return bot2_response


def gen_bot2_response():    
    response_stream = get_characterglm_response(filter_text_msg(st.session_state["bot2_history"]), meta=bot2_meta)
    bot1_response = output_stream_response(response_stream, bot1_placeholder)
    if not bot1_response:
        bot1_placeholder.markdown("生成出错")
        st.session_state["history"].pop()
    else:
        st.session_state["history"].append(TextMsg({"role": "bot1", "content": bot1_response}))
        st.session_state["bot1_history"].append(TextMsg({"role": "user", "content": bot1_response}))
        st.session_state["bot2_history"].append(TextMsg({"role": "assistant", "content": bot1_response}))       
    
start_chat()
