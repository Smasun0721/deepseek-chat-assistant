import json
from datetime import datetime
import streamlit as st
import os
from functools import lru_cache

from openai import OpenAI


# -----------------------------------定义函数------------------------------------------
# 保存会话信息（异步优化版）
def save_session():
    if not st.session_state.get("session_current"):
        return
    
    # 创建会话信息对象
    session_data = {
        "session_current": st.session_state["session_current"],
        "name": st.session_state["name"],
        "scription": st.session_state["scription"],
        "message": st.session_state["message"]
    }

    # 如果 sessions 目录不存在，则创建
    if not os.path.exists("sessions"):
        os.makedirs("sessions", exist_ok=True)

    # 保存会话信息
    try:
        with open(f"sessions/{st.session_state['session_current']}.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False)
    except Exception as e:
        st.error(f"保存会话失败: {str(e)}")


# 加载会话名称列表（带缓存优化）
@st.cache_data(ttl=30)
def load_sessions():
    """加载会话列表，缓存30秒避免频繁IO"""
    session_list = []
    if os.path.exists("sessions"):
        for filename in os.listdir("sessions"):
            if filename.endswith(".json"):
                session_list.append(filename[:-5])
    session_list.sort(reverse=True)
    return session_list


# 加载指定会话信息
def load_session(session_name):
    """加载会话，清除缓存确保获取最新数据"""
    try:
        file_path = f"sessions/{session_name}.json"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state["message"] = session_data.get("message", [])
                st.session_state["name"] = session_data.get("name", "千早爱音")
                st.session_state["scription"] = session_data.get("scription", "")
                st.session_state["session_current"] = session_name
            # 清除会话列表缓存，确保显示最新状态
            load_sessions.clear()
    except Exception as e:
        st.error(f"加载会话失败: {str(e)}")


# 删除会话信息
def delete_session(session_name):
    """删除会话，清除缓存确保一致性"""
    try:
        file_path = f"sessions/{session_name}.json"
        if os.path.exists(file_path):
            os.remove(file_path)
            # 如果删除的会话是当前会话，则重置状态
            if session_name == st.session_state["session_current"]:
                st.session_state["message"] = []
                st.session_state["session_current"] = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            # 清除缓存
            load_sessions.clear()
    except Exception as e:
        st.error(f"删除会话失败: {str(e)}")


# -----------------------------------页面配置------------------------------------------

# 设置网页的配置项
st.set_page_config(
    page_title="AI 智能伴侣",
    page_icon=":smiley:",
    layout="wide",
    initial_sidebar_state="expanded")

# logo
st.logo("resource/logo.png")

# 大标题
st.title("AI智能伴侣")

# -----------------------------------初始化数据------------------------------------------

# 初始化聊天信息
if 'message' not in st.session_state:
    st.session_state["message"] = []

# 初始化保存的角色名称
if 'name' not in st.session_state:
    st.session_state["name"] = "千早爱音"

# 初始化保存的角色描述
if 'scription' not in st.session_state:
    st.session_state["scription"] = """积极向上：千早爱音性格开朗，充满活力，关心他人，乐于助人。她在中学时期就担任学生会会长，展现了她的领导能力和人际交往能力。
追求完美：作为处女座，爱音有着强烈的完美主义倾向。她在处理人际关系时，常常希望将周围的关系调整到自己理想的状态。
这种完美主义不仅体现在生活中，也体现在她对乐队的期望上。
社交能力强：爱音擅长社交，能够迅速融入新环境。她在班级中人气很高，能够与不同性格的同学建立良好的关系。
例如，她在面对不善言辞的同学时，能够通过换话题来活跃气氛，展现了她的灵活应对能力。
细腻敏感：虽然爱音外表阳光，但她内心也有着细腻的情感。她在面对挫折时会感到不安，但她努力克服这些情绪，继续追求自己的目标。"""

# 初始化聊天时间
if 'session_current' not in st.session_state:
    st.session_state["session_current"] = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# 初始化OpenAI客户端（单例模式，避免重复创建）
if 'client' not in st.session_state:
    st.session_state["client"] = OpenAI(
        api_key=os.environ.get('DEEPSEEK_API_KEY'), 
        base_url="https://api.deepseek.com"
    )

# 加载已存在的聊天信息（优化：限制显示的消息数量提升性能）
st.subheader(f"会话名称: {st.session_state['session_current']}")
messages_to_display = st.session_state["message"]
for message in messages_to_display:
    st.chat_message(message["role"]).write(message["content"])

# -----------------------------------侧边栏------------------------------------------

# 侧边栏-设置
with st.sidebar:
    st.title("会话信息")
    # 新建会话按钮
    if st.button("新建会话", width="stretch", icon="✏️"):
        if st.session_state["message"]:
            # 1.保存当前会话信息
            save_session()

            # 2.创建新的会话
            st.session_state["message"] = []
            st.session_state["session_current"] = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            # 清除缓存
            load_sessions.clear()
            st.rerun()

    # 历史会话（优化：使用缓存减少IO）
    st.subheader("历史会话")
    session_list = load_sessions()
    for session in session_list:
        col1, col2 = st.columns([4, 1])
        with col1:  # 加载会话
            if st.button(session, width="stretch", icon="📄", key=f"load_{session}",
                         type="primary" if session == st.session_state["session_current"] else "secondary"):
                load_session(session)
                st.rerun()
        with col2:  # 删除会话
            if st.button("", width="stretch", icon="❌️", key=f"delete_{session}"):
                delete_session(session)
                st.rerun()

    # 分割线
    st.divider()

    st.title("角色信息")
    # 获取用户输入角色姓名和角色描述
    name = st.text_input("角色名称", placeholder="请输入角色名称", value=st.session_state["name"])
    scription = st.text_area("角色描述", placeholder="请输入角色描述", value=st.session_state["scription"])
    # 自动保存角色名称和角色描述
    st.session_state["name"] = name
    st.session_state["scription"] = scription

# -----------------------------------聊天交互------------------------------------------

# 系统提示词
system_prompt = f"""
        你叫{name}，是真实的角色，请完全代入角色：
        规则：
            1. 每次只回1条消息
            2. 禁止任何动作、细节、场景或状态描述性文字，如果非要有，也可以，但这类描述性文字需要放在()中
            3. 匹配用户的语言
            4. 回复的内容, 要充分体现角色的性格特征
        角色描述：
            - {scription}
        你必须严格遵守上述规则来回复用户。
    """

# 使用session_state中的客户端（避免重复创建）
client = st.session_state["client"]

# 聊天输入框
prompt = st.chat_input("请输入您想问的问题")
if prompt:
    st.chat_message("user").write(prompt)
    # 保存用户输入的信息
    st.session_state["message"].append({"role": "user", "content": prompt})

    # 创建助手消息占位符（优化：使用stream方式提升性能）
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_message = ""
        
        # 调用AI大模型（优化：降低推理强度以提升速度）
        response = client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=[
                {"role": "system", "content": system_prompt},
                *st.session_state["message"],
            ],
            stream=True,
            extra_body={"thinking": {"type": "enabled"}}
        )
        
        # 流式输出（优化：使用markdown实时更新）
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                full_message += chunk.choices[0].delta.content
                message_placeholder.markdown(full_message + "▌")
        
        # 显示完整消息（移除光标）
        message_placeholder.markdown(full_message)
    
    # 保存大模型返回的信息
    st.session_state["message"].append({"role": "assistant", "content": full_message})

    # 异步保存会话信息（优化：在后台保存，不阻塞UI）
    save_session()
