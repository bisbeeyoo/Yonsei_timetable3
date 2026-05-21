import streamlit as st
import pandas as pd
import os
import re

# --- 기본 설정 및 데이터 로딩 ---

st.set_page_config(page_title="연세대학교 교육대학원 시간표 도우미", layout="wide")
st.title("👨‍💻 연세대학교 교육대학원 2026학년도 1학기 시간표 도우미")

with st.expander("✨ 주요 기능 및 사용 안내 (클릭하여 확인)"):
    st.subheader("✨ 주요 기능")
    st.info(
        """
        * **실시간 필터링 및 검색**: 전공, 학년, 이수구분 등 다양한 조건으로 수많은 강좌를 실시간으로 필터링하고, 과목명이나 교수명으로 원하는 과목을 즉시 검색할 수 있습니다.

        * **나만의 시간표 시각화**: 과목을 추가하면 즉시 시간표에 시각적으로 반영됩니다. 과목별로 색상이 자동 지정되어 가독성이 높으며, 토/일, 야간 수업 추가 시 시간표가 동적으로 확장됩니다.

        * **강력한 중복 자동 검사 (💡핵심 기능)**
            * **시간 중복 방지**: 현재 시간표와 1분이라도 겹치는 과목은 목록에서 **자동으로 제외**되어, 시간 충돌 없는 완벽한 시간표를 만들 수 있습니다.
            * **과목 중복 방지**: 이미 추가한 과목과 동일한 교과목코드의 다른 분반 역시 목록에서 자동으로 제외됩니다.

        * **URL을 통한 실시간 공유 (🔗 핵심 기능)**
            * 시간표를 완성하면 현재 상태가 **URL에 실시간으로 반영**됩니다. 이 주소를 복사해서 친구에게 보내면, 친구는 내가 만든 시간표를 그대로 볼 수 있습니다.

        * **이미지 저장 및 편의 기능**
            * **이미지 저장**: 완성된 시간표를 깔끔한 `.png` 파일로 다운로드하여 저장하거나 공유할 수 있습니다.
            * **학점 계산**: 선택한 과목들의 총 학점이 실시간으로 자동 계산됩니다.
            * **상세 정보**: 이수구분, 수업/원격 방식, 캠퍼스, 강의실 등 수강에 필요한 모든 정보를 한눈에 제공합니다.
        """
    )
    
    st.subheader("⚠️ 중요 알림")
    st.warning(
        """
        - **데이터 출처:** 본 시간표 정보는 연세대학교 교육대학원 공지 데이터를 기반으로 합니다.
        - **변동 가능성:** 학사 운영상 수업 시간표는 변경될 수 있습니다. **수강 신청 전 반드시 학교 포탈 시스템에서 최종 시간표를 확인**하시기 바랍니다.
        - **책임의 한계:** 본 도우미를 통해 발생할 수 있는 시간표 오류나 수강 신청 불이익에 대해 개발자는 책임을 지지 않습니다.
        """
    )


# --- 색상 팔레트 ---
PREDEFINED_COLORS = [
    "#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3", "#fdb462",
    "#b3de69", "#fccde5", "#d9d9d9", "#bc80bd", "#ccebc5", "#ffed6f",
    "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5", "#c49c94"
]

def ensure_columns(df, required_cols):
    """데이터프레임에 필요한 컬럼이 없으면 빈 문자열로 추가합니다."""
    for col in required_cols:
        if col not in df.columns:
            df[col] = ''

@st.cache_data
def load_and_process_data(file_path):
    """
    yonsei_timetable.csv 파일에서 데이터를 읽고 전처리합니다.
    """
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
    except Exception as e:
        st.error(f"CSV 파일을 읽는 중 오류 발생: {e}")
        return None

    required_cols = ['교과목명', '교수명', '학점', '이수구분', '영역구분', '학부(과)', '대상학년', '분반', '강의시간/강의실', '캠퍼스구분', '교과목코드', '수업방법', '비고', '원격강의구분', 'type']
    ensure_columns(df, required_cols)
    
    # type 컬럼 세팅
    if (df['type'] == '').all() or df['type'].isna().all():
        df['type'] = df['이수구분'].apply(lambda x: '교양' if '교양' in str(x) else '전공')

    df_combined = df[required_cols].copy().dropna(subset=['교과목코드', '분반'])
    df_combined[['대상학년', '영역구분', '비고', '원격강의구분', '수업방법', '학부(과)']] = df_combined[['대상학년', '영역구분', '비고', '원격강의구분', '수업방법', '학부(과)']].fillna('')
    
    df_combined['교과목코드'] = df_combined['교과목코드'].astype(int)
    df_combined['분반'] = df_combined['분반'].astype(int)
    
    def parse_time(time_str):
        if not isinstance(time_str, str): return []
        parsed = []
        pattern = r'([월화수목금토일])([^월화수목금토일]*)'
        matches = re.finditer(pattern, time_str)
        for match in matches:
            day, details = match.group(1), match.group(2)
            room = (re.search(r'\[(.*?)\]', details).group(1) if re.search(r'\[(.*?)\]', details) else '')
            periods = sorted([int(p) for p in re.findall(r'\d+', re.sub(r'\[.*?\]', '', details))])
            if periods: parsed.append({'day': day, 'periods': periods, 'room': room})
        return parsed

    df_combined['parsed_time'] = df_combined['강의시간/강의실'].apply(parse_time)
    
    def create_time_slots_set(parsed_time_list):
        slots = set()
        if not isinstance(parsed_time_list, list): return slots
        for time_info in parsed_time_list:
            for period in time_info['periods']:
                slots.add((time_info['day'], period))
        return slots
    
    df_combined['time_slots_set'] = df_combined['parsed_time'].apply(create_time_slots_set)
    
    return df_combined

def get_available_courses(df, selected_codes):
    if not selected_codes:
        return df

    my_course_codes = {code for code, no in selected_codes}
    available_df = df[~df['교과목코드'].isin(my_course_codes)]

    my_courses_df = df[df.set_index(['교과목코드', '분반']).index.isin(selected_codes)]
    my_busy_slots = set().union(*my_courses_df['time_slots_set'])
    
    if not my_busy_slots:
        return available_df

    is_available_time = available_df['time_slots_set'].apply(lambda course_slots: course_slots.isdisjoint(my_busy_slots))
    return available_df[is_available_time]

def format_course_string(x, mode='selectbox'):
    method_campus_info = ""
    if pd.notna(x['수업방법']) and x['수업방법'].strip() != '':
        if ('대면' in x['수업방법'] or '혼합' in x['수업방법']) and pd.notna(x['캠퍼스구분']) and x['캠퍼스구분'].strip() != '':
            method_campus_info = f"/{x['수업방법']}({x['캠퍼스구분']})"
        else:
            method_campus_info = f"/{x['수업방법']}"
    
    remote_info = ""
    if ('비대면' in x['수업방법'] or '혼합' in x['수업방법']) and pd.notna(x['원격강의구분']) and x['원격강의구분'].strip() != '':
        remote_info = f"({x['원격강의구분']})"

    time_display = x['강의시간/강의실'] if pd.notna(x['강의시간/강의실']) else "시간미지정"
    
    if x['type'] == '전공':
        type_specific_info = f"[{x['대상학년']}/{x['이수구분']}"
    else:
        area_info = f"/{x['영역구분']}" if pd.notna(x['영역구분']) and x['영역구분'].strip() else ""
        type_specific_info = f"[{x['이수구분']}{area_info}"
    
    if mode == 'selectbox':
        formatted_bunban = f"{int(x['분반']):03d}"
        formatted_hakjeom = f"{int(x['학점'])}학점" if x['학점'] == int(x['학점']) else f"{x['학점']}학점"
        professor_info = f"{x['교수명']}, {formatted_bunban}반, {formatted_hakjeom}"
    else:
        professor_info = x['교수명']

    base_str = (f"{type_specific_info}{method_campus_info}{remote_info}] "
                f"{x['교과목명']} ({professor_info}) / {time_display}")
    
    if pd.notna(x['비고']) and x['비고'].strip() != '':
        base_str += f" / 비고: {x['비고']}"
        
    return base_str

def add_course_to_timetable(course_row):
    code, no = course_row['교과목코드'], course_row['분반']
    if (code, no) in st.session_state.my_courses:
        st.warning(f"'{course_row['교과목명']}' 과목은 이미 목록에 있습니다.")
        return

    st.session_state.my_courses.append((code, no))
    if course_row['교과목명'] not in st.session_state.color_map:
        next_color_index = len(st.session_state.color_map) % len(PREDEFINED_COLORS)
        st.session_state.color_map[course_row['교과목명']] = PREDEFINED_COLORS[next_color_index]
    
    st.query_params["courses"] = ",".join([f"{c}-{n}" for c, n in st.session_state.my_courses])
    st.success(f"✅ '{course_row['교과목명']}' 과목을 추가했습니다.")
    st.rerun()


# --- 파일 로드 경로 ---
csv_file_path = 'yonsei_timetable.csv'
if not os.path.exists(csv_file_path):
    st.error(f"'{csv_file_path}' 파일을 찾을 수 없습니다. `app.py`와 같은 폴더에 CSV 파일을 배치해주세요.")
    st.stop()

master_df = load_and_process_data(csv_file_path)

if master_df is not None:
    if 'my_courses' not in st.session_state: st.session_state.my_courses = []
    if 'color_map' not in st.session_state: st.session_state.color_map = {}

    if "courses" in st.query_params and not st.session_state.my_courses:
        try:
            courses_str = st.query_params.get("courses")
            if courses_str:
                shared_courses = []
                for item in courses_str.split(','):
                    if '-' in item:
                        code, no = map(int, item.split('-'))
                        if not master_df[(master_df['교과목코드'] == code) & (master_df['분반'] == no)].empty:
                            shared_courses.append((code, no))
                if shared_courses:
                    st.session_state.my_courses = shared_courses
                    shared_courses_df = master_df[master_df.set_index(['교과목코드', '분반']).index.isin(shared_courses)]
                    for _, course_row in shared_courses_df.iterrows():
                        if course_row['교과목명'] not in st.session_state.color_map:
                            next_color_index = len(st.session_state.color_map) % len(PREDEFINED_COLORS)
                            st.session_state.color_map[course_row['교과목명']] = PREDEFINED_COLORS[next_color_index]
                    st.rerun()
        except (ValueError, IndexError):
            st.error("공유된 URL의 형식이 올바르지 않습니다.")
            st.query_params.clear()

    available_df = get_available_courses(master_df, st.session_state.my_courses)

    st.subheader("1. 과목 선택")
    tab_major, tab_general = st.tabs(["🎓 전공 과목 선택", "📚 교양/공통 과목 선택"])
    
    with tab_major:
        all_majors_df = master_df[master_df['type'] == '전공']
        majors_df_to_display = available_df[available_df['type'] == '전공']
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            department_options = sorted(all_majors_df['학부(과)'].dropna().unique().tolist())
            selected_depts = st.multiselect("전공 학부(과)", department_options, key="depts_multiselect")

        options_df = all_majors_df[all_majors_df['학부(과)'].isin(selected_depts)] if selected_depts else all_majors_df

        with col2:
            grade_options = sorted(options_df['대상학년'].dropna().unique(), key=lambda x: int(re.search(r'\d+', str(x)).group()) if re.search(r'\d+', str(x)) else 99)
            selected_grade = st.selectbox("학년", ["전체"] + grade_options, key="grade_select")

        if selected_grade != "전체": options_df = options_df[options_df['대상학년'] == selected_grade]

        with col3:
            type_options = sorted(options_df['이수구분'].dropna().unique().tolist())
            selected_course_type = st.selectbox("이수구분", ["전체"] + type_options, key="course_type_select")

        if selected_course_type != "전체": options_df = options_df[options_df['이수구분'] == selected_course_type]
            
        with col4:
            major_campus_options = sorted(options_df['캠퍼스구분'].dropna().unique().tolist())
            selected_major_campus = st.selectbox("캠퍼스", ["전체"] + major_campus_options, key="major_campus_select")
            
        with col5:
            credit_options = ['전체'] + sorted(options_df['학점'].dropna().unique())
            selected_credit = st.selectbox("학점", credit_options, key="credit_select", format_func=lambda x: '전체' if x == '전체' else f'{x}학점')

        with st.expander("🕒 빈 시간으로 검색하기 (선택)"):
            time_filter_cols = st.columns(2)
            with time_filter_cols[0]:
                selected_days = st.multiselect('원하는 요일 선택', ['월', '화', '수', '목', '금', '토', '일'], key="filter_days")
            with time_filter_cols[1]:
                selected_periods = st.multiselect('원하는 교시 선택', list(range(0, 16)), key="filter_periods")

        final_filtered_df = majors_df_to_display.copy()
        if selected_depts: final_filtered_df = final_filtered_df[final_filtered_df['학부(과)'].isin(selected_depts)]
        if selected_grade != "전체": final_filtered_df = final_filtered_df[final_filtered_df['대상학년'] == selected_grade]
        if selected_course_type != "전체": final_filtered_df = final_filtered_df[final_filtered_df['이수구분'] == selected_course_type]
        if selected_major_campus != "전체": final_filtered_df = final_filtered_df[final_filtered_df['캠퍼스구분'] == selected_major_campus]
        if selected_credit != '전체': final_filtered_df = final_filtered_df[final_filtered_df['학점'] == selected_credit]

        if selected_days and selected_periods:
            allowed_slots = set((day, period) for day in selected_days for period in selected_periods)
            final_filtered_df = final_filtered_df[final_filtered_df['time_slots_set'].apply(lambda s: s.issubset(allowed_slots) if s else False)]

        search_query = st.text_input("🔎 **과목명 또는 교수명으로 검색**", placeholder="예: 교육학개론 또는 홍길동", key="major_search")
        if search_query:
            q = search_query.lower()
            final_filtered_df = final_filtered_df[final_filtered_df['교과목명'].str.lower().str.contains(q, na=False) | final_filtered_df['교수명'].str.lower().str.contains(q, na=False)]

        st.write("---")

        if not selected_depts:
            st.info("먼저 전공 학부(과)를 선택해주세요.")
        else:
            sorted_df = pd.DataFrame(columns=final_filtered_df.columns)
            if not final_filtered_df.empty:
                temp_df = final_filtered_df.copy()
                temp_df['grade_num'] = temp_df['대상학년'].str.extract(r'(\d+)').astype(float).fillna(99)
                sorted_df = temp_df.sort_values(by=['grade_num', '이수구분', '교과목명'], ascending=[True, False, True])
                        
            if sorted_df.empty:
                st.warning("선택한 조건에 현재 추가 가능한 전공 과목이 없습니다.")
            else:
                st.info(f"**{len(sorted_df)}개**의 과목을 찾았습니다.")
                filter_state_key = f"{''.join(selected_depts)}-{selected_grade}-{selected_course_type}-{selected_major_campus}-{search_query}"

                selected_index = st.selectbox(
                    "추가할 전공 과목 선택",
                    options=sorted_df.index,
                    format_func=lambda idx: format_course_string(sorted_df.loc[idx], mode='selectbox'),
                    key=f"major_select_{filter_state_key}",
                    placeholder="과목을 선택하세요...",
                    label_visibility="collapsed"
                )

                if selected_index is not None:
                    if st.button("전공 추가", key=f"add_major_btn_{filter_state_key}", use_container_width=True):
                        add_course_to_timetable(sorted_df.loc[selected_index])

    with tab_general:
        all_general_df = master_df[master_df['type'] == '교양']
        general_df_to_display = available_df[available_df['type'] == '교양']

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            cat_options = sorted(all_general_df['이수구분'].dropna().unique().tolist())
            selected_cat = st.selectbox("이수구분", ["전체"] + cat_options, key="cat_select")

        options_df = all_general_df[all_general_df['이수구분'] == selected_cat] if selected_cat != "전체" else all_general_df

        with col2:
            area_options = sorted([opt for opt in options_df['영역구분'].dropna().unique() if str(opt).strip()])
            selected_area = st.selectbox("영역구분", ["전체"] + area_options, key="area_select")

        if selected_area != "전체": options_df = options_df[options_df['영역구분'] == selected_area]

        with col3:
            method_options = sorted(options_df['수업방법'].dropna().unique().tolist())
            selected_method = st.selectbox("수업방법", ["전체"] + method_options, key="method_select")
        
        if selected_method != "전체": options_df = options_df[options_df['수업방법'] == selected_method]

        with col4:
            remote_options = sorted([opt for opt in options_df['원격강의구분'].dropna().unique() if str(opt).strip()])
            selected_remote = st.selectbox("원격강의구분", ["전체"] + remote_options, key="remote_select")
        
        if selected_remote != "전체": options_df = options_df[options_df['원격강의구분'] == selected_remote]

        with col5:
            campus_options = sorted(options_df['캠퍼스구분'].dropna().unique().tolist())
            selected_campus = st.selectbox("캠퍼스", ["전체"] + campus_options, key="general_campus_select")
        
        with col6:
            credit_options = ['전체'] + sorted(options_df['학점'].dropna().unique())
            selected_credit = st.selectbox("학점", credit_options, key="gen_credit_select", format_func=lambda x: '전체' if x == '전체' else f'{x}학점')

        with st.expander("🕒 빈 시간으로 검색하기 (선택)"):
            time_filter_cols = st.columns(2)
            with time_filter_cols[0]:
                selected_days = st.multiselect('원하는 요일 선택', ['월', '화', '수', '목', '금', '토', '일'], key="gen_filter_days")
            with time_filter_cols[1]:
                selected_periods = st.multiselect('원하는 교시 선택', list(range(0, 16)), key="gen_filter_periods")

        final_filtered_gen_df = general_df_to_display.copy()
        if selected_cat != "전체": final_filtered_gen_df = final_filtered_gen_df[final_filtered_gen_df['이수구분'] == selected_cat]
        if selected_area != "전체": final_filtered_gen_df = final_filtered_gen_df[final_filtered_gen_df['영역구분'] == selected_area]
        if selected_method != "전체": final_filtered_gen_df = final_filtered_gen_df[final_filtered_gen_df['수업방법'] == selected_method]
        if selected_remote != "전체": final_filtered_gen_df = final_filtered_gen_df[final_filtered_gen_df['원격강의구분'] == selected_remote]
        if selected_campus != "전체": final_filtered_gen_df = final_filtered_gen_df[final_filtered_gen_df['캠퍼스구분'] == selected_campus]
        if selected_credit != '전체': final_filtered_gen_df = final_filtered_gen_df[final_filtered_gen_df['학점'] == selected_credit]

        if selected_days and selected_periods:
            allowed_slots = set((day, period) for day in selected_days for period in selected_periods)
            final_filtered_gen_df = final_filtered_gen_df[final_filtered_gen_df['time_slots_set'].apply(lambda s: s.issubset(allowed_slots) if s else False)]

        search_query = st.text_input("🔎 **과목명 또는 교수명으로 검색**", placeholder="예: 논문작성법 또는 홍길동", key="general_search")
        if search_query:
            q = search_query.lower()
            final_filtered_gen_df = final_filtered_gen_df[final_filtered_gen_df['교과목명'].str.lower().str.contains(q, na=False) | final_filtered_gen_df['교수명'].str.lower().str.contains(q, na=False)]

        st.write("---")
        
        if final_filtered_gen_df.empty:
            st.warning("선택한 조건에 현재 추가 가능한 교양/공통 과목이 없습니다.")
        else:
            sorted_gen_df = final_filtered_gen_df.sort_values(by=['이수구분', '영역구분', '수업방법', '교과목명'], ascending=True)
            st.info(f"**{len(sorted_gen_df)}개**의 과목을 찾았습니다.")

            filter_state_key = f"{selected_cat}-{selected_area}-{selected_method}-{selected_remote}-{selected_campus}-{search_query}"
            selected_index_gen = st.selectbox(
                "추가할 교양 과목 선택",
                options=sorted_gen_df.index,
                format_func=lambda idx: format_course_string(sorted_gen_df.loc[idx], mode='selectbox'),
                key=f"general_select_{filter_state_key}",
                placeholder="과목을 선택하세요...",
                label_visibility="collapsed"
            )

            if selected_index_gen is not None:
                if st.button("교양 추가", key=f"add_gen_btn_{filter_state_key}", use_container_width=True):
                    add_course_to_timetable(sorted_gen_df.loc[selected_index_gen])

    st.divider()
    st.subheader("2. 나의 시간표")

    if not st.session_state.my_courses:
        st.info("과목을 추가하면 시간표가 여기에 표시됩니다.")
    else:
        my_courses_df = master_df[master_df.set_index(['교과목코드', '분반']).index.isin(st.session_state.my_courses)]

        days_order = ['월', '화', '수', '목', '금', '토', '일']
        days_to_display_set = set(['월', '화', '수', '목', '금'])
        for _, course in my_courses_df.iterrows():
            for time_info in course['parsed_time']: days_to_display_set.add(time_info['day'])
        days_to_display = [day for day in days_order if day in days_to_display_set]

        default_min_period, default_max_period = 1, 9
        all_periods = [p for _, course in my_courses_df.iterrows() for time_info in course['parsed_time'] for p in time_info['periods']]
        final_max_period = max(default_max_period, max(all_periods) if all_periods else default_max_period)
        final_min_period = min(default_min_period, min(all_periods) if all_periods else default_min_period)

        timetable_data = {}
        for p in range(final_min_period, final_max_period + 1):
            for d in days_to_display: timetable_data[(p, d)] = {"content": "", "color": "white", "span": 1, "is_visible": True}

        for _, course in my_courses_df.iterrows():
            if course['parsed_time']:
                color = st.session_state.color_map.get(course['교과목명'], "white")
                for time_info in course['parsed_time']:
                    if time_info['day'] not in days_to_display: continue
                    content = f"<b>{course['교과목명']}</b><br>{course['교수명']}<br>{time_info['room']}"
                    periods = sorted(time_info['periods'])
                    if not periods: continue
                    start_period, block_len = periods[0], 1
                    for i in range(1, len(periods)):
                        if periods[i] == periods[i-1] + 1: block_len += 1
                        else:
                            if (start_period, time_info['day']) in timetable_data:
                                timetable_data[(start_period, time_info['day'])].update({"content": content, "color": color, "span": block_len})
                                for j in range(1, block_len):
                                    if (start_period + j, time_info['day']) in timetable_data: timetable_data[(start_period + j, time_info['day'])]["is_visible"] = False
                            start_period, block_len = periods[i], 1
                    if (start_period, time_info['day']) in timetable_data:
                        timetable_data[(start_period, time_info['day'])].update({"content": content, "color": color, "span": block_len})
                        for j in range(1, block_len):
                            if (start_period + j, time_info['day']) in timetable_data: timetable_data[(start_period + j, time_info['day'])]["is_visible"] = False

        day_col_width = (100 - 10) / len(days_to_display)
        table_html = f"""<div id="timetable-to-capture"><table class="timetable"><tr><th width="10%">교시</th>"""
        for d in days_to_display: table_html += f'<th width="{day_col_width}%">{d}</th>'
        table_html += '</tr>'
        time_map = {i: f"{8+i:02d}:00" for i in range(16)}
        for p in range(final_min_period, final_max_period + 1):
            table_html += f'<tr><td>{p}교시<br>{time_map.get(p, "")}</td>'
            for d in days_to_display:
                cell = timetable_data.get((p, d))
                if cell and cell["is_visible"]: table_html += f'<td rowspan="{cell["span"]}" style="background-color:{cell["color"]};">{cell["content"]}</td>'
            table_html += '</tr>'

        untimed_courses = [course for _, course in my_courses_df.iterrows() if not course['parsed_time']]
        if untimed_courses:
            table_html += '<tr><td style="font-weight:bold;">시간 미지정</td>'
            untimed_content = "<br>".join([f"<b>{c['교과목명']}</b> ({c['교수명']})" for c in untimed_courses])
            table_html += f'<td colspan="{len(days_to_display)}" style="text-align: left; padding: 8px; background-color: #f8f9fa; line-height: 1.6;">{untimed_content}</td></tr>'
        table_html += "</table></div>"
        
        button_html = """
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <button id="download-btn-component" class="download-btn">시간표 이미지로 저장</button>
        <div id="status-message" style="margin-top:10px;font-size:14px"></div>
        <script>
            document.getElementById('download-btn-component').onclick = function() {
                const element = document.getElementById("timetable-to-capture");
                const statusDiv = document.getElementById('status-message');
                if (element) {
                    statusDiv.innerText = '이미지 생성 중...';
                    statusDiv.style.color = 'blue';
                    html2canvas(element, { scale: 3, useCORS: true, backgroundColor: '#ffffff' })
                    .then(canvas => {
                        const link = document.createElement("a");
                        link.href = canvas.toDataURL("image/png");
                        link.download = "2026-1학기_시간표.png";
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        statusDiv.innerText = '✅ 이미지 다운로드가 시작되었습니다.';
                        statusDiv.style.color = 'green';
                    }).catch(err => {
                        statusDiv.innerText = '❌ 이미지 생성 오류: ' + err;
                        statusDiv.style.color = 'red';
                    });
                }
            };
        </script>
        """
        
        combined_html = f"""
        <style>
        .timetable{{width:100%;border-collapse:collapse;table-layout:fixed;border-bottom:1px solid #e0e0e0}}
        .timetable th,.timetable td{{border:1px solid #e0e0e0;text-align:center;vertical-align:middle;padding:2px;height:50px;font-size:.75em;overflow:hidden;text-overflow:ellipsis;word-break:keep-all}}
        .timetable th{{background-color:#f0f2f6;font-weight:700}}
        .download-btn{{display:inline-block;padding:10px 20px;background-color:#007bff;color:#fff;text-align:center;text-decoration:none;border-radius:5px;border:none;cursor:pointer;font-size:16px;margin-top:20px}}
        .download-btn:hover{{background-color:#0056b3}}
        </style>
        {table_html}{button_html}
        """
        
        base_height = (final_max_period - final_min_period + 2) * 55 + 120
        extra_height = (55 + (len(untimed_courses) - 1) * 25) if untimed_courses else 0
        st.components.v1.html(combined_html, height=base_height + extra_height)
                        
        st.write("---")

        list_col, action_col = st.columns([0.85, 0.15])
        with list_col:
            num_selected_courses = len(st.session_state.my_courses)
            total_credits = my_courses_df['학점'].sum() if not my_courses_df.empty else 0
            major_credits = my_courses_df[my_courses_df['type'] == '전공']['학점'].sum() if not my_courses_df.empty else 0
            general_credits = my_courses_df[my_courses_df['type'] == '교양']['학점'].sum() if not my_courses_df.empty else 0
            
            f_cred = lambda c: str(int(c)) if c == int(c) else f"{c:.1f}"
            credit_details_parts = []
            if major_credits > 0: credit_details_parts.append(f"전공 {f_cred(major_credits)}학점")
            if general_credits > 0: credit_details_parts.append(f"교양 {f_cred(general_credits)}학점")
            credit_details_str = f" ({', '.join(credit_details_parts)})" if credit_details_parts else ""

            st.markdown(f"""
            <div style="display: flex; align-items: center; height: 40px;">
                <strong style="font-size: 1.1rem; white-space: nowrap;">선택한 과목 내역 [총 {num_selected_courses}과목, {f_cred(total_credits)}학점{credit_details_str}]</strong>
            </div>
            """, unsafe_allow_html=True)

        with action_col:
            if st.button("전체 초기화", type="primary", use_container_width=True):
                st.session_state.my_courses = []
                st.session_state.color_map = {}
                st.query_params.clear()
                st.rerun()

        st.info("시간표를 공유하려면 현재 브라우저의 주소창에 있는 전체 URL을 복사하여 전달하세요.", icon="💡")

        st.markdown("""
        <style>
            .course-list-item::before { content: '●'; font-size: 0.5em; margin-right: 9px; user-select: none; }
        </style>
        """, unsafe_allow_html=True)

        for index, (code, no) in enumerate(st.session_state.my_courses):
            course = master_df[(master_df['교과목코드'] == code) & (master_df['분반'] == no)].iloc[0]
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                display_str = format_course_string(course, mode='list') 
                st.markdown(f"""
                <div style="display: flex; align-items: baseline;" class="course-list-item">
                    <div style="word-break: break-all; overflow-wrap: break-word;">
                        {display_str}
                        <div style="opacity: 0.7;">({code}-{int(no):03d}, {f_cred(course['학점'])}학점)</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                if st.button("제거", key=f"del-{code}-{no}-{index}", use_container_width=True, type="secondary"):
                    st.session_state.my_courses.pop(index)
                    updated_courses_param = ",".join([f"{c}-{n}" for c, n in st.session_state.my_courses])
                    if updated_courses_param: st.query_params["courses"] = updated_courses_param
                    else: st.query_params.clear()
                    st.rerun()
