import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 제품군별 설정 데이터 정의
def get_dimension_defaults(family):
    if family == "Standard":
        return {"길이(mm)": "143.3", "폭(mm)": "50.0", "두께(mm)": "10.0"}
    elif family == "Capsule":
        return {"외경(mm)": "270.0", "내경(mm)": "250.0", "높이(mm)": "30.0"}
    else:  # Flux
        return {"Flux_Value": "243.0", "Density": "1.2", "Viscosity": "0.8"}

# 2. 메인 UI 구성
st.set_page_config(layout="wide")
st.title("통합 성적서 생성 시스템")

tab1, tab2 = st.tabs(["성적서 작성", "대시보드"])

# [TAB 1] 작성 화면
with tab1:
    st.subheader("기본 정보 입력")
    col1, col2 = st.columns(2)
    
    with col1:
        product_family = st.selectbox("제품군 선택", ["Standard", "Capsule", "Flux"])
    with col2:
        doc_number = st.text_input("문서 번호", f"DOC-{datetime.now().strftime('%Y%m%d')}")

    # 선택된 제품군에 따라 치수 항목 로드
    st.subheader(f"치수 검사 ({product_family})")
    defaults = get_dimension_defaults(product_family)
    
    input_data = {}
    with st.form("inspection_form"):
        for key, value in defaults.items():
            input_data[key] = st.text_input(f"{key} (표준치: {value})", value=value)
        
        submitted = st.form_submit_button("성적서 저장")
        
        if submitted:
            # 최종 데이터 구조
            final_record = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "제품군": product_family,
                "문서번호": doc_number,
                **input_data
            }
            
            # 세션에 데이터 누적 (실제 사용 시 DB 저장 로직으로 대체)
            if 'data_log' not in st.session_state:
                st.session_state.data_log = []
            st.session_state.data_log.append(final_record)
            st.success(f"{product_family} 제품군 성적서가 저장되었습니다.")

# [TAB 2] 대시보드 화면
with tab2:
    st.subheader("저장된 데이터 현황")
    if 'data_log' in st.session_state and st.session_state.data_log:
        df = pd.DataFrame(st.session_state.data_log)
        
        # 제품군별 필터링 기능
        filter_family = st.multiselect("제품군 필터", df["제품군"].unique(), default=df["제품군"].unique())
        filtered_df = df[df["제품군"].isin(filter_family)]
        
        st.dataframe(filtered_df, use_container_width=True)
        
        # 다운로드 버튼
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("CSV로 다운로드", csv, "report_data.csv", "text/csv")
    else:
        st.info("아직 저장된 데이터가 없습니다.")
