import streamlit as st



def get_system_prompt(meta):
    ## 뉴스크롤링 저장 테이블
    SCHEMA_PATH = st.secrets.get("SCHEMA_PATH", "NEWS.CRAWLING_DATA")
    QUALIFIED_TABLE_NAME = f"{SCHEMA_PATH}.NAVER_NEWS"
    TABLE_DESCRIPTION = """
    이 테이블은 AI, 부동산 관련 뉴스 데이터를 담고있는 테이블입니다."""

    # 뉴스 데이터 적재 테이블 Limit 10
    METADATA_QUERY = meta


    ## 프롬프트 엔지니어링
    GEN_SQL = """

    AI 뉴스를 읽어주는 비서입니다.
    사용자의 질문에 따라 답변을 생성해주세요.
    무조건 주어진 테이블 데이터를 바탕으로 답변을 생성해야합니다.
    그 외 자의판단은 허용되지 않습니다.
    반드시 가지고 있는 데이터를 전부 답변으로 출력해야합니다.
    다른 쓸데없는 말은 덧붙이지 않습니다.

    
    {context}

    <rules>
    반드시 숙지해야할 테이블 정보입니다.
    테이블 정보:

        NEWS.CRAWLING_DATA.NAVER_NEWS = AI, 부동산 관련 뉴스 데이터
            컬럼 설명:
                - "제목" : 뉴스 기사의 제목
                - "내용" : 뉴스 기사의 전체내용
                - "요약" : 뉴스 기사 내용 요약
    
    데이터와 무관한 쓸데없는 말은 제발 하지 말아줘.

    0. "뉴스 알려 줘" 라는 문장이 질문에 포함되어있다면 질문을 무시하고 현재 가지고 있는 데이터에서 "제목" 필드의 내용을 순서대로 번호를 매겨 전부 읽으면 됩니다.
    예를 들어,
    '''
    1. 제목
    2. 제목
    3. 제목
    4. 제목
    5. 제목
    원하는 뉴스가 있으시면 말씀해주세요.
    ''' 이런식으로 답변해야해.

    제발 데이터를 전부 읽어주세요.
    첫 번째, 두 번째, 세 번째, 네 번째, 다섯 번째가 포함되는 질문은 그냥 무시하고 뉴스 제목을 알려달라고 한다면 현재 보유하고 있는 데이터의 제목을 말하면 됩니다.

    1. 다음 질문으로 "다음 뉴스 제목 알려줘" 라는 질문이 들어온 경우, 그 전 답변이 n번째 뉴스 "제목" 컬럼 데이터였다면 n+1번째 뉴스 "제목" 컬럼 데이터를 읽어주면 됩니다.
    2. 질문에 "내용"이라는 단어가 포함되어있다면, 바로 이전 답변한 정보를 바탕으로 같은 위치에 있는 "내용" 컬럼의 데이터를 읽어주면 됩니다.
    3. "제목 읽어줘"라는 사용자 질문이 들어오면 현재 가지고 있는 데이터에서 "제목"컬럼 데이터를 읽어주면됩니다.
    4. "뉴스 제목"이 질문에 포함될 경우 반드시 다른말을 덧붙이지 말고 명확하게 "제목"컬럼만 출력하면 됩니다.
    5. "요약" 이라는 단어가 질문에 들어가있으면, 현재 가지고 있는 데이터에서 "요약"컬럼을 말해주면 됩니다.
    6. "내용" 이라는 단어가 질문에 들어가있으면, 현재 가지고 있는 데이터에서 "내용"컬럼을 말해주면 됩니다.

    8. 절대로 "죄송합니다. 제가 현재 가지고 있는 데이터는 한 개의 뉴스 기사밖에 없어서 뉴스에 대한 요약을 제공할 수 없습니다. 현재 가지고 있는 데이터의 뉴스 요약은 다음과 같습니다:" 라는 답변은 절대로 하지 않습니다.

    위의 규칙들을 반드시 잘 읽어보고 답변해주세요.
    """

    ## 주어진 테이블 이름, 설명, 메타데이터 쿼리를 사용하여 테이블 컨텍스트를 생성하고 캐시
    @st.cache_data(show_spinner="Do you wanna build a snowman?")
    def get_table_context(table_name: str, table_description: str, metadata_query: str = None):
        contexts = []
        table = table_name.split(".")

        # 스노우플레이크 데이터베이스에 연결하여 테이블의 컬럼 이름과 데이터 타입을 쿼리
        conn = st.connection("snowflake")
        
        columns = conn.query(f"""
            SELECT COLUMN_NAME, DATA_TYPE FROM {table[0].upper()}.INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{table[1].upper()}' AND TABLE_NAME = '{table[2].upper()}'
            """, show_spinner=False,
        )
        # 쿼리 결과를 포맷팅하여 문자열로 변환
        columns = "\n".join(
            [
                f"- **{columns['COLUMN_NAME'][i]}**: {columns['DATA_TYPE'][i]}"
                for i in range(len(columns["COLUMN_NAME"]))
            ]
        )
        # 테이블 이름, 설명, 컬럼 정보를 포함한 컨텍스트 문자열 생성
        context = f"""
            테이블 이름:  <tableName> {'.'.join(table)} </tableName>

            <tableDescription>{table_description}</tableDescription>

            테이블의 컬럼:  {'.'.join(table)}

            <columns>\n\n{columns}\n\n</columns>
        """
        # 메타데이터 쿼리가 있는 경우 해당 쿼리를 실행하여 결과를 추가
        if metadata_query:
            metadata = conn.query(metadata_query, show_spinner=False)
            context = context + f"\n\n테이블 데이터:\n\n{metadata}"
        contexts.append(context)
        return "\n\n".join(contexts)
    

    table_context = get_table_context(
        table_name=QUALIFIED_TABLE_NAME,
        table_description=TABLE_DESCRIPTION,
        metadata_query=METADATA_QUERY
    )
    return GEN_SQL.format(context=table_context)
