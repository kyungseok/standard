import datetime
import io
import pandas as pd
import streamlit as st

# 1. 페이지 기본 설정 (스마트폰 화면 최적화 및 탭 레이아웃 구성)
st.set_page_config(page_title="스마트 출하검사 시스템", layout="centered")

# CSS 스타일 주입: 가독성 및 UI 최적화
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

# 프로그램 내부 데이터베이스 역할을 할 가상 마스터 테이블 초기화 (세션 상태 저장)
if "master_db" not in st.session_state:
    st.session_state.master_db = pd.DataFrame()

# 상단 탭 메뉴 구성
tab1, tab2 = st.tabs(["📝 실시간 검사 입력", "📊 이력 조회 대시보드"])

# ==========================================
# [TAB 1] 실시간 검사 입력 화면 (수정 완료)
# ==========================================
with tab1:
    st.title("📱 스마트 출하검사기록")

    st.subheader("🏢 성적서 및 제품 기본 정보")

    today = datetime.date.today()
    inspection_date = st.date_input("🗓️ 검사일자 (작성일자)", today)
    formatted_today_str = today.strftime("%y-%m-%d")
    default_doc_number = f"AFQEP-901-04-{formatted_today_str}-001"

    # 제품 정보 입력 칸 (지정된 순서 가로 2열 배치)
    info_col1, info_col2 = st.columns(2)

    with info_col1:
        doc_number = st.text_input("문서번호", value=default_doc_number)
        part_number = st.text_input("P/N (품명)", value="MLC-P50-B2PV31")

        option_list = ["C1", "C2", "C3", "E3", "C7", "C8", "E8", "CE", "-"]
        product_option = st.selectbox("옵션", option_list, index=8)

        engraving = st.text_input("인각", value="-")
        prod_qty = st.number_input("생산 수량(PCS)", value=200, step=1)

    with info_col2:
        inspector_list = ["이완희", "조경석", "김민우", "이홍규"]
        inspector = st.selectbox("검사자", inspector_list, index=1)

        lot_number = st.text_input("LOT No.", value="BCL05-3010")

        sealing_list = ["FEP", "EPDM", "SILICONE", "VITONE", "-"]
        sealing_selection = st.selectbox("Sealing", sealing_list, index=4)

        customer = st.text_input("고객사", value="-")
        # [수정] 출하수량(숫자) -> 여재배열(문자 입력) 변경
        media_array = st.text_input("여재배열", value="-")

    st.divider()

    # 판정용 마스터 변수
    total_pass = True
    saved_data = {
        "문서번호": doc_number,
        "검사일자": str(inspection_date),
        "검사자": inspector,
        "P/N (품명)": part_number,
        "LOT No.": lot_number,
        "옵션": product_option,
        "Sealing": sealing_selection,
        "인각": engraving,
        "고객사": customer,
        "생산수량": prod_qty,
        "여재배열": media_array,  # [수정] 데이터 저장용 딕셔너리 키/값 변경
    }

    # --- 1구역. 제품 외관 검사 ---
    st.subheader("✨ 1. 제품 외관 검사")
    visual_product_items = [
        "Burr, Weld Line, Flow Mark",
        "미성형, 이물, 얼룩",
        "찍힘, 흑점, Scratch",
        "Adapter Code 사양",
        "Bridge, End Cap 접착 상태",
    ]
    with st.expander("👁️ 제품 외관 항목 확인 (기본값: O)", expanded=True):
        for p_item in visual_product_items:
            col_txt, col_btn = st.columns(2)
            with col_txt:
                st.write(f"• {p_item}")
            with col_btn:
                p_res = st.radio(
                    "판정",
                    ["O (양호)", "X (불량)"],
                    index=0,
                    key=f"prod_{p_item}",
                    label_visibility="collapsed",
                    horizontal=True,
                )
                saved_data[f"[제품외관] {p_item}"] = p_res
                if p_res == "X (불량)":
                    total_pass = False

    st.divider()

    # 💡 [핵심 수정] 여기서부터 아래의 모든 코드가 tab1 내부에 속하도록 한 칸씩 들여쓰기(Indent) 처리되었습니다.
    # --- 2구역. 치수 검사 ---
    st.subheader("📊 2. 치수 항목 측정 (N=5)")
    dimension_defaults = {
        "길이 치수": {"spec": "243.0", "tol": "1.0"},
        "외경 치수 (OD)": {"spec": "68.0", "tol": "1.0"},
        "내경 치수 (ID)": {"spec": "30.0", "tol": "1.0"},
        "실링 외경": {"spec": "45.0", "tol": "0.3"},
        "동진/SK마이크로웍스_산 높이(㎜)": {"spec": "", "tol": ""},
        "동진/SK마이크로웍스_산수(개)": {"spec": "", "tol": ""},
        "동진/SK마이크로웍스_절단 길이 (㎜)": {"spec": "", "tol": ""},
    }
    sample_count = 5

    for item, defaults in dimension_defaults.items():
        with st.expander(f"🔍 {item}", expanded=True):
            col_spec, col_tol = st.columns(2)
            with col_spec:
                spec_input = st.text_input(
                    f"{item} 기준치", value=defaults["spec"], key=f"spec_{item}"
                )
            with col_tol:
                tol_input = st.text_input(
                    f"{item} 관리공차(±)", value=defaults["tol"], key=f"tol_{item}"
                )

            st.write("**측정치 입력**")
            cols_meas = st.columns(5)
            meas_list = []

            for i in range(sample_count):
                with cols_meas[i]:
                    meas_input = st.text_input(
                        f"N{i+1}", key=f"meas_{item}_{i}", placeholder="0.0"
                    )
                    meas_list.append(meas_input)

                    if meas_input.strip():
                        try:
                            val = float(meas_input)
                            spec = float(spec_input)
                            tol = float(tol_input)
                            if (spec - tol) <= val <= (spec + tol):
                                st.markdown(
                                    "<div class='pass-box'>합격</div>",
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.markdown(
                                    "<div class='ng-box'>NG</div>",
                                    unsafe_allow_html=True,
                                )
                                total_pass = False
                        except ValueError:
                            st.markdown(
                                "<div class='ng-box'>오류</div>",
                                unsafe_allow_html=True,
                            )
                            total_pass = False
                    else:
                        st.markdown(
                            "<div class='empty-box'>-</div>",
                            unsafe_allow_html=True,
                        )

            saved_data[f"[치수] {item} 기준"] = spec_input
            saved_data[f"[치수] {item} 공차"] = tol_input
            for i, m_val in enumerate(meas_list):
                saved_data[f"[치수] {item} N{i+1}"] = m_val

    st.divider()

    # --- 3구역. 포장 검사 항목 ---
    st.subheader("📦 3. 포장 검사 항목")
    visual_pack_items = [
        "변색(Discolor)",
        "포장 상태 확인",
        "Tape 접착 상태 확인",
        "Label 잔사 확인",
        "포장내 이물 확인",
        "제품 Label 인쇄사양 및 부착위치 확인",
        "Gift Box Label 인쇄사양 및 부착위치 확인",
        "Carton Box Label 인쇄사양 및 부착위치 확인",
    ]
    with st.expander("👁️ 포장 외관 항목 확인 (기본값: O)", expanded=True):
        for pack_item in visual_pack_items:
            col_txt, col_btn = st.columns(2)
            with col_txt:
                st.write(f"• {pack_item}")
            with col_btn:
                pack_res = st.radio(
                    "판정",
                    ["O (양호)", "X (불량)"],
                    index=0,
                    key=f"pack_{pack_item}",
                    label_visibility="collapsed",
                    horizontal=True,
                )
                saved_data[f"[포장외관] {pack_item}"] = pack_res
                if pack_res == "X (불량)":
                    total_pass = False

    st.divider()

    # --- 4구역. 최종 종합 결과 및 마스터 누적 저장 ---
    st.subheader("🏆 최종 결과 판정")
    final_status = "PASS" if total_pass else "NG"
    saved_data["최종종합판정"] = final_status

    if total_pass:
        st.success(f"🎉 종합판정결과: 최종 합격 (PASS)")
    else:
        st.error(f"🚨 종합판정결과: 최종 불합격 (NG 발생)")

    if st.button("💾 이 검사 기록을 마스터 DB에 누적 저장", type="primary"):
        new_row = pd.DataFrame([saved_data])
        st.session_state.master_db = pd.concat(
            [st.session_state.master_db, new_row], ignore_index=True
        )
        st.success(
            f"🚀 [LOT No: {lot_number}] 데이터가 마스터 데이터베이스에 안전하게 저장되었습니다!"
        )

# ==========================================
# [TAB 2] 이력 조회 대시보드 화면
# ==========================================
with tab2:
    st.title("📊 품질 이력 관리 대시보드")

    db = st.session_state.master_db

    if db.empty:
        st.info("데이터베이스가 비어 있습니다. 먼저 검사 입력 화면에서 데이터를 저장해 주세요.")
    else:
        total_records = len(db)
        pass_records = len(db[db["최종종합판정"] == "PASS"])
        ng_records = len(db[db["최종종합판정"] == "NG"])
        pass_rate = (pass_records / total_records) * 100

        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.metric("총 검사 건수", f"{total_records}건")
        with m_col2:
            st.metric("합격 수(PASS)", f"{pass_records}건")
        with m_col3:
            st.metric("불합격 수(NG)", f"{ng_records}건")
        with m_col4:
            st.metric("최종 합격률", f"{pass_rate:.1f}%")

        st.divider()

        st.subheader("🔍 데이터 필터링 검색")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            search_lot = st.text_input("검색할 LOT No. 입력")
        with f_col2:
            search_inspector = st.selectbox(
                "검사자별 필터", ["전체보기"] + inspector_list
            )

        filtered_db = db.copy()

        if search_lot.strip():
            filtered_db = filtered_db[
                filtered_db["LOT No."].str.contains(search_lot, na=False)
            ]

        if search_inspector != "전체보기":
            filtered_db = filtered_db[
                filtered_db["검사자"] == search_inspector
            ]

        st.write(f"📋 조회 결과 (총 {len(filtered_db)}건)")
        st.dataframe(filtered_db)

        st.divider()

        # --- 문서 내보내기 구역 (해결책 2: 세로 카드 적층 방식 PDF 엔진) ---
        st.subheader("📥 성적서 문서 내보내기")

        import io
        import os
        import pandas as pd
        from datetime import datetime
        from reportlab.lib.pagesizes import letter, landscape, A4  # 가로 한계가 없으므로 표준 A4 세로 규격 사용
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from openpyxl.utils import get_column_letter
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfgen import canvas

        # 1. 실시간 오늘 날짜 반영 파일명 정의
        today_str = datetime.today().strftime('%Y%m%d')
        excel_filename = f"{today_str}_품질이력대장.xlsx"
        pdf_filename = f"{today_str}_품질이력대장.pdf"

        # 표준 A4 세로 규격 수치 안전 추출
        a4_width, a4_height = letter  # 가로 612, 세로 792 픽셀 안전 규격

        # 2. 운영체제별 한글 폰트 경로 순회 엔진 안정화
        font_candidates = [
            os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Fonts', 'malgun.ttf'),
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
            os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Microsoft', 'Windows', 'Fonts', 'malgun.ttf')
        ]

        font_name = 'Helvetica'
        for p_path in font_candidates:
            if os.path.exists(p_path):
                try:
                    pdfmetrics.registerFont(TTFont('CustomKoreanFont', p_path))
                    font_name = 'CustomKoreanFont'
                    break
                except Exception:
                    continue

        # 3. 엑셀 버퍼 생성 및 열 너비 자동 조절 (엑셀은 가로 스크롤이 편하므로 기존 명품 로직 유지)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            filtered_db.to_excel(writer, index=False, sheet_name="품질이력")
            worksheet = writer.sheets["품질이력"]
    
            for col_idx, col_name in enumerate(filtered_db.columns, start=1):
                col_letter = get_column_letter(col_idx)
                max_len = len(str(col_name).encode('utf-8'))
        
                for val in filtered_db[col_name]:
                    if pd.notna(val):
                        val_str = str(val)
                        byte_len = len(val_str.encode('utf-8'))
                        display_len = len(val_str) + (byte_len - len(val_str)) // 2
                        if display_len > max_len:
                            max_len = display_len
                    
                worksheet.column_dimensions[col_letter].width = max(max_len + 3, 10)

        excel_buffer.seek(0)

        # 4. PDF 하단 중앙 실시간 총 페이지 번호 산출용 클래스
        class NumberedCanvas(canvas.Canvas):
            def __init__(self, *args, **kwargs):
                super(NumberedCanvas, self).__init__(*args, **kwargs)
                self._saved_page_states = []

            def showPage(self):
                self._saved_page_states.append(dict(self.__dict__))
                self._startPage()

            def save(self):
                num_pages = len(self._saved_page_states)
                for state in self._saved_page_states:
                    self.__dict__.update(state)
                    self.draw_page_number(num_pages)
                    super(NumberedCanvas, self).showPage()
                super(NumberedCanvas, self).save()

            def draw_page_number(self, page_count):
                self.saveState()
                self.setFont(font_name, 9)
                self.setFillColor(colors.HexColor('#6B7280'))
                page_text = f"{self._pageNumber} / {page_count}"
                self.drawCentredString(a4_width / 2.0, 0.4 * inch, page_text)
                self.restoreState()

        # 5. PDF 데이터 가로 쓰기 래핑 및 테이블 빌드
        pdf_buffer = io.BytesIO()
        margin = 0.5 * inch

        # 가로 제약이 없으므로 표준 A4 세로 템플릿 마스터 적용
        doc = SimpleDocTemplate(
            pdf_buffer, 
            pagesize=(a4_width, a4_height),
            leftMargin=margin, rightMargin=margin,
            topMargin=margin, bottomMargin=margin
        )
        elements = []
        styles = getSampleStyleSheet()

        # 대형 타이틀 서식 (세련된 기업형 인디고 블루)
        title_style = ParagraphStyle(
            'PDFTitleStyle',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=22,
            leading=26,
            alignment=1,
            textColor=colors.HexColor('#1E3A8A'),
            spaceAfter=15
        )

        # 카드 내부 서식 정의
        card_label_style = ParagraphStyle(
            'CardLabel',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=9,
            leading=12,
            alignment=0, # 왼쪽 정렬
            textColor=colors.HexColor('#4B5563') # 진한 회색 (항목명용)
        )

        card_value_style = ParagraphStyle(
            'CardValue',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=9,
            leading=12,
            alignment=0, # 왼쪽 정렬
            textColor=colors.HexColor('#111827') # 다크블랙 (데이터값용)
        )

        # 성적서 상단 메인 제목 추가
        elements.append(Paragraph("품질이력 성적서 (기록대장 요약본)", title_style))
        elements.append(Spacer(1, 10))

        # --- 🛠️ [해결책 2 핵심] 행별 독립식 2열 구조 성적서 카드 적층 생성 ---
        available_width = a4_width - (2 * margin)
        col_widths = [available_width * 0.45, available_width * 0.55] # 항목명 45%, 측정값 55% 분배

        for idx, row in filtered_db.iterrows():
            # 성적서 데이터 한 행당 하나의 미니 테이블(카드) 생성
            card_data = []
    
            # 카드 최상단에 일련번호 타이틀 행 삽입
            card_title_style = ParagraphStyle(
                'CardTitle', fontName=font_name, fontSize=10, leading=14, 
                textColor=colors.white, alignment=0
            )
            # 식별하기 좋은 기준값(문서번호 혹은 일련번호) 추출
            doc_id = row.get('문서번호', row.get('검사일자', f"No.{idx+1}"))
            card_data.append([
                Paragraph(f"<b>■ 품질 기록 검사 건 - ID: {doc_id}</b>", card_title_style), 
                Paragraph("", card_title_style)
            ])
    
            # 40여개의 모든 컬럼 명과 실제 값을 세로로 한 항목씩 추가
            for col_name in filtered_db.columns:
                val = row[col_name]
                val_str = str(val) if pd.notna(val) else "-"
        
                card_data.append([
                    Paragraph(f"• {col_name}", card_label_style),
                    Paragraph(val_str, card_value_style)
                ])
    
            # 성적서 카드 개별 디자인 선언
            row_table = Table(card_data, colWidths=col_widths)
            row_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')), # 카드의 머리말 색상
                ('SPAN', (0, 0), (1, 0)),                                    # 머리말 행 합치기
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]), # 내부 지브라 스트라이프
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')), # 은은한 회색 격자
                ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#1E3A8A')),  # 카드 전체 외곽 테두리
            ]))
    
            # 하나의 카드가 페이지 중간에 애매하게 쪼개져 넘어가지 않도록 KeepTogether로 패킹
            elements.append(KeepTogether([
                row_table,
                Spacer(1, 15) # 카드와 카드 사이 여백 조절
            ]))

        doc.build(elements, canvasmaker=NumberedCanvas)
        pdf_buffer.seek(0)

        # 6. Streamlit UI 다운로드 버튼 배치
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="🟢 최적화 엑셀 다운로드",
                data=excel_buffer,
                file_name=excel_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with col2:
            st.download_button(
                label="🔴 카드형 PDF 다운로드",
                data=pdf_buffer,
                file_name=pdf_filename,
                mime="application/pdf"
            )
