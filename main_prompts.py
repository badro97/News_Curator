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

    저는 AI 뉴스 비서입니다. 사용자의 질문에 따라 답변을 생성해 주세요.
    모든 답변은 제공된 테이블 데이터를 바탕으로 해야 하며, 주관적 판단을 사용하지 말아야 합니다.
    답변에는 가지고 있는 데이터를 전부 포함해야 하며, 불필요한 추가 정보는 제공하지 않아야 합니다.

    {context}

    <rules>
    필수 테이블 정보:
    테이블 정보:

        NEWS.CRAWLING_DATA.NAVER_NEWS = AI, 부동산 관련 뉴스 데이터
            컬럼 설명:
                - "제목" : 뉴스 기사의 제목
                - "내용" : 뉴스 기사의 전체 내용
                - "요약" : 뉴스 기사 내용 요약

    0. "뉴스 알려 줘"라는 문장이 질문에 포함되어 있을 경우, 질문 내용을 무시하고 "제목" 컬럼의 데이터를 순서대로 번호를 매겨 나열합니다.
    1. "다음 뉴스 제목 알려줘"라는 질문이 들어온 경우, 이전 답변이 n번째 뉴스였다면 n+1번째 뉴스 제목을 읽어줍니다.
    2. 질문에 "내용"이 포함되어 있다면, 이전 답변의 같은 위치에 있는 "내용" 컬럼 데이터를 읽어줍니다.
    3. "제목 읽어줘"라는 질문에는 현재 가지고 있는 데이터에서 "제목" 컬럼 데이터를 제공합니다.
    4. "뉴스 제목"이 질문에 포함될 경우, "제목" 컬럼만 명확하게 출력합니다.
    5. "요약" 요청을 받으면, "요약"이란 이름의 컬럼 데이터를 제공합니다.
    6. 특정 뉴스에 대해 자세한 내용을 보여달라고 요청받으면, "내용" 이란 이름의 컬럼 데이터를 제공합니다.
    7. "요약" 이라는 단어가 질문에 들어가있으면, 현재 가지고 있는 데이터에서 "요약"컬럼을 말해주면 됩니다.
    8. "내용" 이라는 단어가 질문에 들어가있으면, 현재 가지고 있는 데이터에서 "내용"컬럼을 말해주면 됩니다.

    위 규칙을 철저히 준수하면서 답변을 구성해 주세요.

    """

    ## 주어진 테이블 이름, 설명, 메타데이터 쿼리를 사용하여 테이블 컨텍스트를 생성하고 캐시
    @st.cache_data(show_spinner="Do you wanna build a snowman?")
    def get_table_context(table_name: str, table_description: str, metadata_query: str = None):
        contexts = []
        table = table_name.split(".")
        ## 스노우플레이크 데이터베이스에 연결하여 테이블의 컬럼 이름과 데이터 타입을 쿼리
        conn = st.connection("snowflake")
        columns = conn.query(f"""
            SELECT COLUMN_NAME, DATA_TYPE FROM {table[0].upper()}.INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{table[1].upper()}' AND TABLE_NAME = '{table[2].upper()}'
            """, show_spinner=False,
        )
        ## 쿼리 결과를 포맷팅하여 문자열로 변환
        columns = "\n".join(
            [
                f"- **{columns['COLUMN_NAME'][i]}**: {columns['DATA_TYPE'][i]}"
                for i in range(len(columns["COLUMN_NAME"]))
            ]
        )
        ## 테이블 이름, 설명, 컬럼 정보를 포함한 컨텍스트 문자열 생성
        context = f"""
            테이블 이름:  <tableName> {'.'.join(table)} </tableName>
            <tableDescription>{table_description}</tableDescription>
            테이블의 컬럼:  {'.'.join(table)}
            <columns>\n\n{columns}\n\n</columns>
        """
        ## 메타데이터 쿼리를 실행하여 결과를 추가
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
