# News_Curator
인공지능설계 기말팀과제 웹 배포용

# AI_Design

#### 전체적인 구조
1. prompts.py에서 답변 양식 프롬프트 조정, 테이블 메타데이터 저장
2. 저장한 테이블 메타데이터를 기반으로 prompts.py의 get_system_prompt에서 Snowflake에서 테이블 가져옴
3. 사용자 입력(질문)을 바탕으로 해당 테이블 상세 쿼리 생성 및 답변 내용에 포함
4. 생성한 쿼리 Snowflake에서 실행한 결과를 포함하여 GPT API에서 최종 답변 출력


#### 선행 되어야 할 것
- 데이터 크롤링 및 1차 전처리 후 테이블 형태(데이터프레임)로 Snowflake 적재


#### 추가 및 개선 필요
- 타 API 연동 (STT, TTS)
- 챗봇 UI 답변의 불완정성
- 데이터 쿼리 후처리
- Streamlit UX/UI


#### 확인 필요한 것
- Github이용한 Streamlit 퍼블릭 웹 배포 시 API연동 정상 작동하는지?