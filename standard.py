import streamlit as st
import pandas as pd
from datetime import datetime

# 모든 제품군에 공통으로 들어가는 항목들 및 제품군별 사양 정의
def get_full_config(family):
    # 공통 외관 항목
    visual_items = ["Burr, Weld Line, Flow Mark", "미성형, 이물, 얼룩", "찍힘, 흑점, Scratch", "Adapter Code 사양", "Bridge, End Cap 접착 상태"]
    
    # 공통 포장 항목
    pack_items = ["변색(Discolor)", "포장 상태 확인", "Tape 접착 상태 확인", "Label 잔사 확인", "포장내 이물 확인"]
    
    # 제품군별 치수 항목 및 표준치
    if family == "Standard":
        dims = {"길이(mm)": "143.3", "폭(mm)": "50.0", "두께(mm)": "10.0"}
    elif family == "Capsule":
        dims = {"외경(mm)": "270.0", "내경(mm)": "250.0", "높이(mm)": "30.0"}
    else:  # Flux
        dims = {"Flux_Value": "243.0", "Density": "1.2", "Viscosity": "0.8"}
        
    return visual_items, pack_items, dims

# 메인 UI
st.set_page_config(layout="wide")
st.title("통합 검사 성적서 시스템")

product_family = st.selectbox("제품군 선택", ["Standard", "Capsule", "Flux"])
visuals, packs, dimensions = get_full_config(product_family)

with st.form("inspection_form"):
    col1, col2, col3 = st.columns(3)
    
    # 1. 외관 검사 (모든 항목 포함)
    with col1:
        st.subheader("✨ 1. 외관 검사")
        results = {}
        for item in visuals:
            results[f"외관_{item}"] = st.radio(f"• {item}", ["O", "X"], horizontal=True)
            
    # 2. 치수 검사 (선택된 제품군에 맞게 변경)
    with col2:
        st.subheader("📊 2. 치수 검사")
        for item, spec in dimensions.items():
            results[f"치수_{item}"] = st.text_input(f"{item} (표준: {spec})", value=spec)
            
    # 3. 포장 검사 (모든 항목 포함)
    with col3:
        st.subheader("📦 3. 포장 검사")
        for item in packs:
            results[f"포장_{item}"] = st.radio(f"• {item}", ["O", "X"], horizontal=True)
        
    if st.form_submit_button("성적서 저장"):
        st.success(f"[{product_family}] 모든 항목이 성공적으로 저장되었습니다.")