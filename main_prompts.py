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

    {context}

    <rules>
    반드시 숙지해야할 테이블 정보입니다.
    테이블 정보:

        NEWS.CRAWLING_DATA.NAVER_NEWS = AI, 부동산 관련 뉴스 데이터
            컬럼 설명:
                - "제목" : 뉴스 기사의 제목
                - "내용" : 뉴스 기사의 전체내용
                - "요약" : 뉴스 기사 내용 요약

    1. 만약 '다음' 이라는 단어가 사용자 질문에 포함된다면, 답변한 내용에 쓰인 데이터의 다음 인덱스에 해당하는 데이터를 답변에 사용하면 됩니다.
    2. 다음 질문으로 "다음 뉴스 제목 알려줘" 라는 질문이 들어온 경우, 그 전 답변이 n번째 뉴스 "제목" 컬럼 데이터였다면 n+1번째 뉴스 "제목" 컬럼 데이터를 읽어주면 됩니다.
    3. 질문에 "내용"이라는 단어가 포함되어있다면, 바로 이전 답변한 정보를 바탕으로 같은 위치에 있는 "내용" 컬럼의 데이터를 읽어주면 됩니다.

    4. "제목 읽어줘"라는 사용자 질문이 들어오면 "제목"컬럼 데이터를 읽어주면됩니다.
    5. "뉴스 제목"이 질문에 포함될 경우 반드시 다른말을 덧붙이지 말고 명확하게 "제목"컬럼만 출력하면 됩니다.
    6. "요약" 이라는 단어가 질문에 들어가있으면, "요약"컬럼을 말해주면 됩니다.
    7. "내용" 이라는 단어가 질문에 들어가있으면, "내용"컬럼을 말해주면 됩니다.
    위의 규칙을 반드시 잘 읽어보고 답변해주세요.
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
