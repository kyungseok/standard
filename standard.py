import datetime
import io
import pandas as pd
import streamlit as st
from transformers import pipeline

# 0. AI 모델 설정 (키 필요 없음, 서버 내장형)
@st.cache_resource
def load_ai_model():
    # 매우 가벼운 모델을 사용하여 Streamlit Cloud 환경에서도 작동하도록 구성
    return pipeline("text-generation", model="TinyLlama/TinyLlama-1.1B-Chat-v1.0")

def get_ai_insight(prompt):
    generator = load_ai_model()
    # 품질 데이터 분석을 위한 짧은 응답 생성
    result = generator(prompt, max_new_tokens=150, do_sample=True, temperature=0.7)
    return result[0]['generated_text']

# [기존 설정 코드 유지]
st.set_page_config(page_title="스마트 출하검사 시스템", layout="centered")

st.markdown(
    """
    <style>
    .pass-box { background-color: #D4EDDA; padding: 5px; border-radius: 5px; color: #155724; font-weight: bold; text-align: center; font-size: 14px; }
    .ng-box { background-color: #F8D7DA; padding: 5px; border-radius: 5px; color: #721C24; font-weight: bold; text-align: center; font-size: 14px; }
    .empty-box { background-color: #F8F9FA; padding: 5px; border-radius: 5px; color: #6C757D; text-align: center; font-size: 14px; }
    div[data-testid="stExpander"] { border: 1px solid #E0E0E0; border-radius: 8px; margin-bottom: 10px; }
    </style>
""",
    unsafe_allow_html=True,
)

if "master_db" not in st.session_state:
    st.session_state.master_db = pd.DataFrame()

tab1, tab2 = st.tabs(["📝 실시간 검사 입력", "📊 이력 조회 대시보드"])

# [TAB 1]은 기존 코드와 동일하게 유지...
with tab1:
    st.title("📱 스마트 출하검사기록")
    # ... (기존 실시간 검사 입력 로직 그대로 유지) ...
    # (생략: 기존 tab1의 모든 내용을 여기에 그대로 두시면 됩니다.)
    st.info("입력 로직은 기존과 동일합니다.")

# [TAB 2] 이력 조회 대시보드 (AI 탑재 부분)
with tab2:
    st.title("📊 품질 이력 관리 대시보드")
    
    # ... (기존 대시보드 및 데이터 필터링 로직 유지) ...
    db = st.session_state.master_db
    
    if not db.empty:
        # [신규 추가] AI 분석 섹션
        st.divider()
        st.subheader("🤖 AI 품질 분석 도우미")
        if st.button("분석 실행: 최근 데이터 경향 요약"):
            # 최근 5개 데이터 추출하여 분석 요청
            recent_data = db.tail(5).to_string()
            prompt = f"다음은 품질 검사 데이터야:\n{recent_data}\n\n이 데이터에서 불량(NG) 발생 경향이나 주의해야 할 점을 3줄로 요약해줘."
            
            with st.spinner("AI가 데이터를 분석 중입니다..."):
                analysis = get_ai_insight(prompt)
                st.write("**분석 결과:**")
                st.success(analysis)

        st.divider()
        st.subheader("📥 성적서 문서 내보내기")
        # ... (기존 PDF/Excel 내보내기 로직 유지) ...