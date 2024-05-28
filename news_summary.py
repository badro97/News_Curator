## 뉴스 내용 요약 및 중복제거

from openai import OpenAI
import snowflake.connector
from snowflake.connector.pandas_tools import pd_writer
from snowflake.connector.pandas_tools import write_pandas
import os
import pandas as pd

def summary_api():
    # db 접근
    ## 접속 인자
    snow_conn = snowflake.connector.connect(
        user=os.getenv('user'),
        password=os.getenv('password'),
        account=os.getenv('account'),
        role=os.getenv('role'),
        warehouse=os.getenv('warehouse'),
        database=os.getenv('database'),
        schema=os.getenv('schema')
    )
    snowCur = snow_conn.cursor()

    ## query 세팅(수정)
    query = '''Select "검색어", "아이디", "제목", "내용", "발행일", "요약"
    From NEWS.CRAWLING_DATA.NAVER_NEWS;'''

    ## query 조회
    snowCur.execute(query) 
    data = snowCur.fetchall()
    columns = [desc[0] for desc in snowCur.description]
    df = pd.DataFrame(data, columns=columns)
    
    # 요약
    ## openai 접속정보
    openai_api_key = st.secrets.OPENAI_API_KEY
    client = OpenAI(api_key=openai_api_key)

    ## init prompt
    prompt = '''
    뉴스를 읽고 mask를 채워줘.
    
    [뉴스]
    {content}
    
    [요약문]
    서론 : mask
    본론 : mask
    결론 : mask
    '''

    ## summary
    ids = df["아이디"].to_list()
    df["요약"] = "" 
    summary_to_id = {}
    ## (수정)
    for id in ids:
        messages = []
        messages.append({"role":"system", "content": "당신은 주어진 틀에 맞춰 뉴스를 요약해주는 챗봇입니다. user가 뉴스를 입력하면 mask에 정보를 입력해주세요."})

        content = df[df["아이디"] == id]["내용"].values[0]
        input_prompt = prompt.format(content=content)
        
        messages.append({"role":"user", "content": input_prompt})
        response = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
        response.choices[0]
        msg = response.choices[0].message.content
    
        # 문자열을 줄바꿈 문자로 분리
        sections = msg.split('\n')
        
        # 각 섹션에서 내용만 추출
        try:
            extracted_contents = ' '.join([section.split(' : ')[1] for section in sections if section])
        except:
            extracted_contents = msg
        df.loc[df['아이디'] == id, '요약'] = extracted_contents

    
    print(len(df), "개의 요약문을 입력하였습니다.")
    
    df['내용'] = df['내용'].apply(lambda x: x.replace('\n','.').replace('..', '.'))
    df['요약'] = df['요약'].apply(lambda x: x.replace('\n','.').replace('..', '.'))
    
    write_pandas(snow_conn, df, 'NAVER_NEWS', auto_create_table=False, overwrite=True)
    snow_conn.close()
    
    return df

df = summary_api()


