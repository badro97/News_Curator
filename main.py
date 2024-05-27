## chatbot
import re
import os
import sys
import streamlit as st
from streamlit_mic_recorder import mic_recorder, speech_to_text
from openai import OpenAI
from gtts import gTTS
import base64
import tempfile
from io import BytesIO
# from pydub import AudioSegment
# from pydub.playback import play
# from pydub import effects
# from dotenv import load_dotenv
# load_dotenv(verbose=True)
from main_prompts import get_system_prompt
header = st.container()
header.title("💬 뉴스 큐레이터")
header.markdown("<div style='color: gray; padding: 10px; margin: 10px;'> 뉴스를 음성으로 간편하게!", unsafe_allow_html=True)
header.markdown(
    """
    <div style='color: #03417F; background-color:#E8F2FC; padding: 10px; margin: 10px;'>
    <li>음성 질문을 인식하고 음성 답변을 출력하는 챗봇입니다.</li>
    <li>AI, 부동산 관련 뉴스 데이터를 담고있습니다.</li>
    </div>
    """, unsafe_allow_html=True)
header.write("""<div class='fixed-header'/>""", unsafe_allow_html=True)

### Custom CSS for the sticky header
st.markdown(
    """
<style>
    div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {
        position: sticky;
        top: 2.875rem;
        background-color: white;
        z-index: 999;
    }
    .fixed-header {
        border-bottom: 1px solid black;
    }
</style>
    """, unsafe_allow_html=True)

# keywords 리스트 초기화
if "keywords" not in st.session_state:
    st.session_state["keywords"] = []


def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio controls autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)



## 키워드 추출 함수
import re

class Extractor:
    def __init__(self):
        self.stored_index = None
    def extract_keyword(self, text):
    
        pattern = re.compile(r"(?:오늘의\s*|오늘\s*)?(.*?)\s*뉴스")
        match = pattern.search(text)
        
        keyword = None
        index = None
        
        if match:
            keyword = match.group(1).strip()
            if keyword.endswith("번째"):
                index_map = {
                    '첫': 0, '두': 1, '세': 2, '네': 3, '다섯': 4,
                    '여섯': 5, '일곱': 6, '여덟': 7, '아홉': 8, '열': 9
                }
                prefix = keyword.split()[0]
                index = index_map.get(prefix, None)
                self.stored_index = index  
            if "다음" in text and self.stored_index is not None:
                self.stored_index += 1  
                index = self.stored_index
    
        return keyword, index
    
extract = Extractor()


## 답변 생성 함수
def complete(questions, prompt):
    res =  client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
                {"role": "system", "content": prompt},
                {"role":"user", "content": f"{questions}"}
            ],
    )
    response = res.choices[0].message.content
    return response

openai_api_key = st.secrets.OPENAI_API_KEY
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "좌측 사이드바의 Start recording 버튼을 눌러 질문해주세요"}]

with st.sidebar:
    text = speech_to_text(language='ko', use_container_width=True, just_once=True, key='STT')
    st.markdown(
    """
    <div style='color: #03417F; background-color:#e0e0eb; padding: 10px; margin: 10px;'>
    <p><strong>Start recording</strong> 버튼을 누르면 음성 녹음이 시작됩니다.</p>
    <p>질문이 끝나면 <strong>Stop recording</strong> 버튼을 눌러 녹음을 종료해주세요.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<h3 style='padding: 10px; margin: 10px;'> 질문 예시", unsafe_allow_html=True)
    st.markdown(
    """
    <li><strong>AI</strong> 뉴스 알려줘</li>
    <li><strong>부동산</strong> 뉴스 알려줘</li>
    <li><strong>N 번째</strong> 뉴스 제목 알려줘</strong></li>
    <li><strong>N 번째</strong> 뉴스 <strong>요약</strong>해 줘</li>
    </div>
    """, unsafe_allow_html=True)

    

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if text:
    keyword, index = extract.extract_keyword(text)
    stored_index = extract.stored_index
    print(stored_index) 
    # st.write(f"주제: {keyword}")
    # st.write(f"인덱스: {index}")
    st.session_state["keywords"].append(keyword)

    st.session_state["keywords"][-1] = st.session_state["keywords"][-1].replace('인공지능', 'AI')
    # st.write(f"현재 키워드 목록: {st.session_state['keywords']}")

    
    if keyword not in ['AI', '부동산']:
        latest_keyword = st.session_state["keywords"][-2]
    else:
        latest_keyword = st.session_state["keywords"][-1]

    meta = f"""
        SELECT
            "제목",
            "내용",
            "요약"
        FROM NEWS.CRAWLING_DATA.NAVER_NEWS
        WHERE "검색어"='{latest_keyword}'
        LIMIT 10;
    """


    client = OpenAI(api_key=openai_api_key)
    st.session_state.messages.append({"role": "user", "content": text})
    
    st.chat_message("user").write(text)
    msg = complete(text, get_system_prompt(meta))
    
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
    conn = st.connection("snowflake")
    df = conn.query(meta)
    st.dataframe(df)
    
    if msg:
        sound_file = BytesIO()
        tts = gTTS(text=msg, lang='ko', slow=False)
        tts.write_to_fp(sound_file)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_file.write(sound_file.getvalue())
            temp_file_path = temp_file.name

        autoplay_audio(temp_file_path)
        os.remove(temp_file_path)
        if not st.session_state["keywords"][-1] in ['AI','부동산']:
            st.session_state["keywords"].pop()

        ## 속도 조절
        # sound_file.seek(0)
        # say = AudioSegment.from_file(sound_file, format="mp3")
        # say_speed = say.speedup(
        # playback_speed=1.25, chunk_size=150, crossfade=25)
        # play(say_speed)
