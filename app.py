import streamlit as st
import pandas as pd
import re

# --- 기본 설정 및 데이터 로딩 ---
st.set_page_config(page_title="연세대학교 교육대학원 시간표 도우미", layout="wide")
st.title("👨‍💻 연세대학교 교육대학원 2026학년도 1학기 시간표 도우미")

with st.expander("✨ 주요 기능 및 사용 안내 (클릭하여 확인)"):
    st.subheader("✨ 주요 기능")
    st.info(
        """
        * **실시간 필터링 및 검색**: 세부 전공, 이수구분(교직/전공/선택) 등 다양한 조건으로 강좌를 실시간 필터링하고, 과목명이나 교수명으로 원하는 과목을 즉시 검색할 수 있습니다.
        * **나만의 시간표 시각화**: 과목을 추가하면 즉시 시간표에 시각적으로 반영됩니다. 과목별로 색상이 자동 지정되어 가독성이 높습니다.
        * **강력한 중복 자동 검사 (💡핵심 기능)**
            * **시간 중복 방지**: 현재 시간표와 1분이라도 겹치는 과목은 목록에서 **자동으로 제외**되어, 시간 충돌 없는 완벽한 시간표를 만들 수 있습니다.
            * **과목 중복 방지**: 이미 추가한 과목과 동일한 교과목코드의 과목 역시 목록에서 자동으로 제외됩니다.
        * **URL을 통한 실시간 공유 (🔗 핵심 기능)**
            * 시간표를 완성하면 현재 상태가 **URL에 실시간으로 반영**됩니다. 이 주소를 복사해서 친구에게 보내면 내 시간표를 그대로 볼 수 있습니다.
        """
    )
    st.subheader("⚠️ 중요 알림")
    st.warning(
        """
        - **데이터 출처:** 본 시간표 정보는 연세대학교 교육대학원 수강편람 데이터를 기반으로 내장되었습니다.
        - **변동 가능성:** 학사 운영상 수업 시간표는 변경될 수 있으므로, **수강 신청 전 반드시 학교 연세포탈서비스에서 최종 시간표를 확인**하시기 바랍니다.
        """
    )

# --- 색상 팔레트 ---
PREDEFINED_COLORS = [
    "#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3", "#fdb462",
    "#b3de69", "#fccde5", "#d9d9d9", "#bc80bd", "#ccebc5", "#ffed6f",
    "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5", "#c49c94"
]

# --- 139개 전체 데이터 내장 (Hardcoded DataFrame) ---
@st.cache_data
def load_yonsei_data():
    raw_data = [
        [1,"교직일반_논문","전학기","대면수업","한국교육의 역사","교직","SPG6824","01",2,2,0,"이원재","신촌캠퍼스","월1[교302]","",""],
        [2,"교직일반_논문","전학기","대면수업","교사의인식및실천연구","교직","SPG6858","01",2,2,0,"임웅","신촌캠퍼스","화1[교304]","","영어강의"],
        [3,"교직일반_논문","전학기","대면수업","교육자를위한인공지능입문","교직","SPG6867","01",2,2,0,"강근영","신촌캠퍼스","목1[교302]","",""],
        [4,"교직일반_논문","전학기","대면수업","학습과학","교직","SPG6862","01",2,2,0,"이희승","신촌캠퍼스","화1[교310]","",""],
        [5,"교직일반_논문","전학기","대면수업","연세와교사의사명","교직","SPG6860","01",2,2,0,"곽호철","신촌캠퍼스","월3[교603]","",""],
        [6,"교직일반_논문","전학기","대면수업","박물관교육","교직","SPG6864","01",2,2,0,"국성하","신촌캠퍼스","화3[교405]","",""],
        [7,"교직일반_논문","전학기","대면수업","교사론","교직","SPG6863","01",2,2,0,"국성하","신촌캠퍼스","목3[교404]","",""],
        [8,"교직일반_논문","전학기","대면수업","교육현장을위한문학읽기","교직","SPG6869","01",2,2,0,"곽수범","신촌캠퍼스","월3[교601]","",""],
        [9,"교직일반_논문","전학기","대면수업","교육과일의세계","교직","SPG6838","01",2,2,0,"한수정","신촌캠퍼스","화3[교302]","",""],
        [10,"교직일반_논문","전학기","대면수업","교육자를위한인공지능과코딩기초","교직","SPG6868","01",2,2,0,"한수연","신촌캠퍼스","목3[교304]","","영어강의"],
        [11,"교직일반_논문","전학기","대면수업","인공지능시대의과학기술과교육","교직","SPG6859","01",2,2,0,"임웅","신촌캠퍼스","화3[교304]","","영어강의"],
        [12,"교직일반_논문","전학기","대면수업","학습동기","교직","SPG6853","01",2,2,0,"김은주","신촌캠퍼스","화3[위204]","",""],
        [13,"교직일반_논문","전학기","대면수업","영재교육의이론과실제","교직","SPG6831","01",2,2,0,"윤성로","신촌캠퍼스","화3[교306]","",""],
        [14,"교직이론및교직소양(교원자격증)-3,4","전학기","대면수업","평생교육프로그램개발론","교직","SPL6691","001",2,2,0,"최유연","신촌캠퍼스","화1[교402]","",""],
        [15,"교직이론및교직소양(교원자격증)-3,4","전학기","대면수업","평생교육실습","교직","SPL6692","001",2,2,0,"한수정","신촌캠퍼스","목1[교404]","",""],
        [16,"교직이론및교직소양(교원자격증)-3,4","전학기","대면수업","평생교육론","교직","SPL6650","001",2,2,0,"이상오","신촌캠퍼스","화1[교404]","",""],
        [17,"교직이론및교직소양(교원자격증)-3,4","전학기","대면수업","평생교육방법론","교직","SPL6690","001",2,2,0,"임현민","신촌캠퍼스","목1[교402]","",""],
        [18,"교직이론및교직소양(교원자격증)-3,4","전학기","대면수업","평생교육경영론","교직","SPL6684","001",2,2,0,"신경석","신촌캠퍼스","화1[교405]","",""],
        [19,"교육공학","전학기","대면수업","교수학습이론","전공","SET6602","01",2,2,0,"이명근","신촌캠퍼스","월1[교606]","",""],
        [20,"교육공학","전학기","대면수업","AI교육공학기초","전공","SET6608","01",2,2,0,"김남주","신촌캠퍼스","화1[교606]","",""],
        [21,"교육공학","전학기","대면수업","원격교육론","선택","SET6652","01",2,2,0,"이지영","신촌캠퍼스","목1[교606]","",""],
        [22,"교육공학","전학기","대면수업","교육공학연구자료분석","선택","SET6678","01",2,2,0,"박종화","신촌캠퍼스","월3[교606]","",""],
        [23,"교육공학","전학기","대면수업","기업교육공학연구","선택","SET6673","01",2,2,0,"백평구","신촌캠퍼스","화3[교606]","",""],
        [24,"교육행정","전학기","대면수업","다문화교육현장사례연구","선택","SMI6522","01",2,2,0,"박순용","신촌캠퍼스","화1[교519]","","구:교육현장연구방법"],
        [25,"교육행정","전학기","대면수업","교육정치학","선택","SEM7814","01",2,2,0,"박대권","신촌캠퍼스","화3[백S113]","",""],
        [26,"교육행정","전학기","대면수업","대학행정론","선택","SEM7787","01",2,2,0,"이인서","신촌캠퍼스","목3[백S206]","",""],
        [27,"국어교육","전학기","대면수업","문학이론","전공","SKE6501","01",2,2,0,"조강석","신촌캠퍼스","월1[백S608]","",""],
        [28,"국어교육","전학기","대면수업","현대비평문학교육론","선택","SKE6554","01",2,2,0,"임유경","신촌캠퍼스","화1[백S604]","",""],
        [29,"국어교육","전학기","대면수업","국어이해교육론","교직","SKE6594","01",2,2,0,"곽수범","신촌캠퍼스","목1[교304]","",""],
        [30,"국어교육","전학기","대면수업","한국구전동화읽기","선택","SKE6561","01",2,2,0,"김영희","신촌캠퍼스","월1[백S604]","",""],
        [31,"국어교육","전학기","대면수업","언어학이론","선택","SKE6541","01",2,2,0,"조운성","신촌캠퍼스","월3[백S604]","",""],
        [32,"국어교육","전학기","대면수업","국어정책론","선택","SKE6577","01",2,2,0,"조태린","신촌캠퍼스","화3[백S604]","",""],
        [33,"국어교육","전학기","대면수업","고전기초강독","전공","SKE6507","01",2,2,0,"이미라","신촌캠퍼스","목3[백S604]","",""],
        [34,"다문화국제이해교육","전학기","대면수업","세계시민교육과지속가능발전","선택","SMI6529","01",2,2,0,"박수연","신촌캠퍼스","월1[백S206]","",""],
        [35,"다문화국제이해교육","전학기","대면수업","다문화교육현장사례연구","선택","SMI6522","01",2,2,0,"박순용","신촌캠퍼스","화1[교519]","","구:교육현장연구방법"],
        [36,"다문화국제이해교육","전학기","대면수업","다문화사회의학교교육","전공","SMI6503","01",2,2,0,"차보은","신촌캠퍼스","목1[교601]","",""],
        [37,"다문화국제이해교육","전학기","대면수업","지역사회와사회통합","선택","SMI6525","01",2,2,0,"오덕열","신촌캠퍼스","목3[교306]","",""],
        [38,"사서교육","전학기","대면수업","학교도서관의최근동향","선택","SLI6579","01",2,2,0,"김기영","신촌캠퍼스","월1[위416]","",""],
        [39,"사서교육","전학기","대면수업","인공지능의이해","선택","SLI6581","01",2,2,0,"송민,이수빈","신촌캠퍼스","화1[위416]","",""],
        [40,"사서교육","전학기","대면수업","목록학","전공","SLI6504","01",2,2,0,"조성원","신촌캠퍼스","목1[위416]","",""],
        [41,"사서교육","전학기","대면수업","장서구성론","선택","SLI6567","01",2,2,0,"안다인","신촌캠퍼스","월3[위416]","",""],
        [42,"사서교육","전학기","대면수업","학술커뮤니케이션론","선택","SLI6545","01",2,2,0,"김승희","신촌캠퍼스","화3[위416]","",""],
        [43,"상담교육","전학기","대면수업","상담이론과실제","전공","SCE6506","01",2,2,0,"서영석","신촌캠퍼스","월1[교405]","",""],
        [44,"상담교육","전학기","대면수업","행동수정","교직","SCE6593","01",2,2,0,"정경미","신촌캠퍼스","화1[백S111]","",""],
        [45,"상담교육","전학기","대면수업","상담교육연구방법","전공","SCE6504","01",2,2,0,"이규민","신촌캠퍼스","목1[교603]","",""],
        [46,"상담교육","전학기","대면수업","집단상담","전공","SCE6505","01",2,2,0,"고성숙","신촌캠퍼스","목1[백S108]","",""],
        [47,"상담교육","전학기","대면수업","집단상담","전공","SCE6505","02",2,2,0,"박남숙","신촌캠퍼스","목1[백S108]","",""],
        [48,"상담교육","전학기","대면수업","상담실습및사례연구","선택","SCE6577","01",2,2,0,"안하얀","신촌캠퍼스","월3[백S108]","",""],
        [49,"상담교육","전학기","대면수업","진로상담","선택","SCE6573","01",2,2,0,"양현정","신촌캠퍼스","화3[백S111]","",""],
        [50,"상담교육","전학기","대면수업","아동발달","교직","SCE6591","01",2,2,0,"이현아","신촌캠퍼스","목3[백S111]","",""],
        [51,"상담교육","전학기","대면수업","특수아상담","교직","SCE6594","01",2,2,0,"이아영","신촌캠퍼스","화3[백S402]","",""],
        [52,"수학교육","전학기","대면수업","수학교육연구방법론","선택","SME6561","01",2,2,0,"임웅","신촌캠퍼스","월1[교304]","",""],
        [53,"수학교육","전학기","대면수업","미분기하","전공","SME6502","01",2,2,0,"양민석","신촌캠퍼스","화1[과225]","",""],
        [54,"수학교육","전학기","대면수업","선형대수","선택","SME6545","01",2,2,0,"윤명호","신촌캠퍼스","월3[과225]","",""],
        [55,"수학교육","전학기","대면수업","수학교재연구및지도법","교직","SME6592","01",2,2,0,"한수연","신촌캠퍼스","화3[교603]","",""],
        [56,"역사교육","전학기","대면수업","중국고중세사탐구","선택","SHE6534","01",2,2,0,"차혜원","신촌캠퍼스","월1[백S503]","",""],
        [57,"역사교육","전학기","대면수업","역사학과논술교육","교직","SHE6593","01",2,2,0,"오정현","신촌캠퍼스","화1[백S503]","",""],
        [58,"역사교육","전학기","대면수업","한국현대사와분단체제","선택","SHE6547","01",2,2,0,"김성보","신촌캠퍼스","목1[백S503]","",""],
        [59,"역사교육","전학기","대면수업","한국중세지성사","선택","SHE6528","01",2,2,0,"도현철","신촌캠퍼스","월3[백S503]","",""],
        [60,"영양교육","전학기","대면수업","식품학특론","전공","SNT6602","01",2,2,0,"채선희","신촌캠퍼스","월1[백S402]","",""],
        [61,"영양교육","전학기","대면수업","영양생리학특론","선택","SNT6665","01",2,2,0,"임주원","신촌캠퍼스","화1[백S402]","",""],
        [62,"영양교육","전학기","대면수업","식품위생학특론","선택","SNT6656","01",2,2,0,"석용희","신촌캠퍼스","목1[백S402]","",""],
        [63,"영양교육","전학기","대면수업","영양과면역","선택","SNT6675","01",2,2,0,"김우기","신촌캠퍼스","월3[백S402]","",""],
        [64,"영양교육","전학기","대면수업","통계분석및실습","선택","SNT6671","01",2,2,0,"김지영","신촌캠퍼스","화3[교516]","",""],
        [65,"영어교육","전학기","대면수업","영국문학개관","전공","SEE6504","01",2,2,0,"김재철","신촌캠퍼스","월1[백S408]","",""],
        [66,"영어교육","전학기","대면수업","영어교재연구및지도법","교직","SEE6592","01",2,2,0,"김미자","신촌캠퍼스","화1[백S408]","",""],
        [67,"영어교육","전학기","대면수업","영어리터러시교수법","선택","SEE6584","01",2,2,0,"이민진","신촌캠퍼스","목1[백S404]","",""],
        [68,"영어교육","전학기","대면수업","영어구조론","선택","SEE6564","01",2,2,0,"박홍근","신촌캠퍼스","목1[백S408]","",""],
        [69,"영어교육","전학기","대면수업","영어교육론","교직","SEE6591","01",2,2,0,"이희경","신촌캠퍼스","월3[교306]","",""],
        [70,"영어교육","전학기","대면수업","영어교육평가","선택","SEE6579","01",2,2,0,"이희경","신촌캠퍼스","화3[교517]","",""],
        [71,"영어교육","전학기","대면수업","영어어휘및문법지도법","교직","SEE6585","01",2,2,0,"최현규","신촌캠퍼스","목3[백S408]","",""],
        [72,"외국어로서의한국어교육","전학기","대면수업","한국어교육과정설계","교직","STK6596","01",2,2,0,"강승혜","신촌캠퍼스","월1[교402]","",""],
        [73,"외국어로서의한국어교육","전학기","대면수업","한국어의이해","전공","STK6602","01",2,2,0,"유현경","신촌캠퍼스","화1[백S106]","",""],
        [74,"외국어로서의한국어교육","전학기","대면수업","대조언어학","선택","STK6554","01",2,2,0,"원미진","신촌캠퍼스","목1[백S106]","",""],
        [75,"외국어로서의한국어교육","전학기","대면수업","한국어문법교육론","선택","STK6537","01",2,2,0,"강현화","신촌캠퍼스","화1[백S106]","",""],
        [76,"외국어로서의한국어교육","전학기","대면수업","한국문화의이해","선택","STK6546","01",2,2,0,"김찬호","신촌캠퍼스","월3[백S106]","",""],
        [77,"외국어로서의한국어교육","전학기","대면수업","한국어교육실습","교직","STK6595","01",2,2,0,"조인옥","신촌캠퍼스","화3[백S106]","",""],
        [78,"외국어로서의한국어교육","전학기","대면수업","한국어능력평가","선택","STK6574","01",2,2,0,"김경선","신촌캠퍼스","목3[백S106]","",""],
        [79,"유아교육","전학기","대면수업","유아교육연구방법","전공","SCH6604","01",2,2,0,"유영미","신촌캠퍼스","월1[삼206]","",""],
        [80,"유아교육","전학기","대면수업","유아교육과정연구","전공","SCH6603","01",2,2,0,"신윤승","신촌캠퍼스","화1[삼206]","",""],
        [81,"유아교육","전학기","대면수업","유아교사교육론","교직","SCH6694","01",2,2,0,"변수연","신촌캠퍼스","목1[삼206]","",""],
        [82,"유아교육","전학기","대면수업","유아교육및보육프로그램연구","교직","SCH6698","01",2,2,0,"신혜영","신촌캠퍼스","화1[삼B110]","",""],
        [83,"유아교육","전학기","대면수업","유아언어교육연구","선택","SCH6641","01",2,2,0,"이하연","신촌캠퍼스","월3[삼B110]","",""],
        [84,"유아교육","전학기","대면수업","유아놀이이론및교육","선택","SCH6644","01",2,2,0,"조항린","신촌캠퍼스","화3[삼B110]","",""],
        [85,"유아교육","전학기","대면수업","영유아발달및교육","전공","SCH6602","01",2,2,0,"김재희","신촌캠퍼스","목3[삼206]","",""],
        [86,"유아교육","전학기","대면수업","비교유아교육세미나","선택","SCH6671","01",2,2,0,"김재희","신촌캠퍼스","월3[삼206]","",""],
        [87,"음악교육","전학기","대면수업","서양음악사(Ⅰ)","전공","SMU6505","01",2,2,0,"김현주","신촌캠퍼스","월1[음404]","",""],
        [88,"음악교육","전학기","대면수업","음악분석및형식론","선택","SMU6559","01",2,2,0,"이홍석","신촌캠퍼스","화1[음102]","",""],
        [89,"음악교육","전학기","대면수업","화성법","전공","SMU6501","01",2,2,0,"송무경","신촌캠퍼스","월1[음420]","",""],
        [90,"음악교육","전학기","대면수업","음악교재연구및지도법","교직","SMU6591","01",2,2,0,"장지원","신촌캠퍼스","월1[음413]","",""],
        [91,"음악교육","전학기","대면수업","음악감상","선택","SMU6651","01",2,2,0,"정종열","신촌캠퍼스","화1[음413]","",""],
        [92,"음악교육","전학기","대면수업","국악개론","전공","SMU6602","01",2,2,0,"최선아","신촌캠퍼스","월3[음413]","",""],
        [93,"음악교육","전학기","대면수업","장구반주법","선택","SMU6545","01",2,2,0,"김진혁","신촌캠퍼스","화1[교101]","",""],
        [94,"인적자원개발","전학기","대면수업","성인학습이론","전공","SHR6505","01",2,2,0,"오석영","신촌캠퍼스","월1[교603]","",""],
        [95,"인적자원개발","전학기","대면수업","인적자원개발과인공지능","선택","SHR7519","01",2,2,0,"이호진","신촌캠퍼스","화1[백S504]","",""],
        [96,"인적자원개발","전학기","대면수업","인적자원개발프로그램평가","선택","SHR6563","01",2,2,0,"양숙형","신촌캠퍼스","목1[백S504]","",""],
        [97,"인적자원개발","전학기","대면수업","일터학습세미나","선택","SHR6586","01",2,2,0,"김혁","신촌캠퍼스","월3[백S504]","",""],
        [98,"인적자원개발","전학기","대면수업","인적자원개발연구자료분석","교직","SHR6591","01",2,2,0,"장지현","신촌캠퍼스","화3[백S504]","",""],
        [99,"인적자원개발","전학기","대면수업","기업문화와교육","선택","SHR7116","01",2,2,0,"박재현","신촌캠퍼스","목3[백S504]","",""],
        [100,"일반사회교육","전학기","대면수업","경제와사회","전공","SSE6503","01",2,2,0,"이상헌","신촌캠퍼스","화1[백S509]","",""],
        [101,"일반사회교육","전학기","대면수업","사회학특강","선택","SSE6539","01",2,2,0,"장상철","신촌캠퍼스","목1[백S509]","",""],
        [102,"일반사회교육","전학기","대면수업","사회조사방법","전공","SSE6506","01",2,2,0,"김종우","신촌캠퍼스","월3[백S509]","",""],
        [103,"일반사회교육","전학기","대면수업","사회정책론","선택","SSE6536","01",2,2,0,"왕혜숙","신촌캠퍼스","화3[백S509]","",""],
        [104,"일반사회교육","전학기","대면수업","일반사회교재연구","교직","SSE6593","01",2,2,0,"윤민희","신촌캠퍼스","목3[백S509]","",""],
        [105,"조기영어교육","전학기","대면수업","조기영어교육과통계학","선택","SEC6711","01",2,2,0,"이민진","신촌캠퍼스","월1[백S404]","",""],
        [106,"조기영어교육","전학기","대면수업","조기영어교육연구방법론","전공","SEC6701","01",2,2,0,"이희경","신촌캠퍼스","화1[교517]","",""],
        [107,"조기영어교육","전학기","대면수업","영어학개론","전공","SEC6606","01",2,2,0,"김현우","신촌캠퍼스","목1[백S204]","",""],
        [108,"조기영어교육","전학기","대면수업","음성음운론과영어발음교육","전공","SEC6602","01",2,2,0,"이석재","신촌캠퍼스","화3[외326-1]","",""],
        [109,"조기영어교육","전학기","대면수업","영어교육학특강","교직","SEC6694","01",2,2,0,"이명신","신촌캠퍼스","목3[백S204]","",""],
        [110,"종교교육","전학기","대면수업","종교와문화","선택","SRE6552","01",2,2,0,"김정형","신촌캠퍼스","월1[백S204]","",""],
        [111,"종교교육","전학기","대면수업","기독교교수-학습과정론","교직","SRE6597","01",2,2,0,"황인혜","신촌캠퍼스","화1[백S204]","",""],
        [112,"종교교육","전학기","대면수업","종교교육사","선택","SRE6557","01",2,2,0,"최은택","신촌캠퍼스","월3[백S204]","",""],
        [113,"종교교육","전학기","대면수업","종교교육론","전공","SRE6602","01",2,2,0,"장윤석","신촌캠퍼스","화3[백S204]","",""],
        [114,"체육및여가교육","전학기","대면수업","운동생리학","전공","SPE6501","01",2,2,0,"서상훈","신촌캠퍼스","월1[스포츠109]","",""],
        [115,"체육및여가교육","전학기","대면수업","체육교육론","교직","SPE6597","01",2,2,0,"이한주","신촌캠퍼스","화1[스포츠315/구기장]","",""],
        [116,"체육및여가교육","전학기","대면수업","스포츠마케팅","선택","SPE6577","01",2,2,0,"이준성","신촌캠퍼스","목1[스포츠109]","",""],
        [117,"체육및여가교육","전학기","대면수업","여가학의질적연구방법론","선택","SPE6612","01",2,2,0,"이철원","신촌캠퍼스","월1[스포츠108]","",""],
        [118,"체육및여가교육","전학기","대면수업","체육교재연구및지도법","교직","SPE6596","01",2,2,0,"권정아","신촌캠퍼스","월3[스포츠109]","",""],
        [119,"체육및여가교육","전학기","대면수업","운동상해재활","선택","SPE6576","01",2,2,0,"이세용","신촌캠퍼스","화3[스포츠108]","",""],
        [120,"체육및여가교육","전학기","대면수업","스포츠카운셀링","선택","SPE6573","001",2,2,0,"윤용진","신촌캠퍼스","목3[스포츠108]","",""],
        [121,"체육및여가교육","전학기","대면수업","뉴스포츠현장조사연구","선택","SPE6578","01",2,2,0,"허진무","신촌캠퍼스","화3[스포츠109/구기장]","",""],
        [122,"통합과학교육","전학기","대면수업","지질학","선택","SGS6832","01",2,2,0,"이기현","신촌캠퍼스","월1[과S222]","",""],
        [123,"통합과학교육","전학기","대면수업","일반지구과학및실험","전공","SGS6704","01",2,2,0,"한원식,송인선","신촌캠퍼스","화1[과S222]","",""],
        [124,"통합과학교육","전학기","대면수업","전자기학","전공","SGS6705","01",2,2,0,"조두희","신촌캠퍼스","목1[과326]","",""],
        [125,"통합과학교육","전학기","대면수업","통합과학교육론","교직","SGS6695","01",2,2,0,"박태윤,장수철","신촌캠퍼스","월3[교311]","",""],
        [126,"통합과학교육","전학기","대면수업","통합과학교육논리및논술","교직","SGS6693","01",2,2,0,"박태윤,장수철","신촌캠퍼스","화3[교311]","",""],
        [127,"통합과학교육","전학기","대면수업","분자생물학","선택","SGS6831","01",2,2,0,"최광민","신촌캠퍼스","목3[과S118A]","",""],
        [128,"통합과학교육","전학기","대면수업","무기화학","전공","SGS6707","01",2,2,0,"안현서","신촌캠퍼스","월3[과523]","",""],
        [129,"통합과학교육","전학기","대면수업","일반생물학및실험","전공","SGS6703","01",2,2,0,"이태호","신촌캠퍼스","화3[과S118A]","",""],
        [130,"평생교육경영","전학기","대면수업","평생교육경영학","전공","SLE7508","01",2,2,0,"이상오","신촌캠퍼스","월1[교410]","",""],
        [131,"평생교육경영","전학기","대면수업","평생교육경영연구방법론","전공","SLE7506","01",2,2,0,"한수정","신촌캠퍼스","화1[교308]","",""],
        [132,"평생교육경영","전학기","대면수업","평생교육의학습조직론","선택","SLE7555","01",2,2,0,"최유연","신촌캠퍼스","월3[교304]","",""],
        [133,"평생교육경영","전학기","대면수업","평생교육의질적연구방법","선택","SLE7545","01",2,2,0,"홍원표","신촌캠퍼스","화3[교601]","",""],
        [134,"평생교육경영","전학기","대면수업","성인학습및상담론","선택","SLE7564","01",2,2,0,"임수원","신촌캠퍼스","목3[교517]","",""],
        [135,"AI융합교육","전학기","대면수업","빅데이터와교육","선택","SAE6521","01",2,2,0,"한수연","신촌캠퍼스","월1[교517]","",""],
        [136,"AI융합교육","전학기","대면수업","AI활용융합교육방법","선택","SAE6527","01",2,2,0,"한수연","신촌캠퍼스","화1[교603]","",""],
        [137,"AI융합교육","전학기","대면수업","인공지능기술과윤리","선택","SAE6526","01",2,2,0,"임웅","신촌캠퍼스","월3[교517]","",""],
        [138,"AI융합교육","전학기","대면수업","딥러닝입문","선택","SAE6525","01",2,2,0,"박헌우","신촌캠퍼스","화3[교614]","",""],
        [139,"공통","전학기","대면수업","연구방법론","전공","SPG6001","001",2,2,0,"미정","신촌캠퍼스","토11","","원격수업상세참조"]
    ]
    
    cols = ['순번','학부(과)','대상학년','수업방법','교과목명','이수구분','교과목코드','분반','학점','이론','실습','교수명','캠퍼스구분','강의시간/강의실','원격강의구분','비고']
    df = pd.DataFrame(raw_data, columns=cols)
    
    # 시간 파싱 함수
    def parse_time(time_str):
        if not isinstance(time_str, str) or not time_str.strip(): return []
        parsed = []
        pattern = r'([월화수목금토일])([^월화수목금토일]*)'
        matches = re.finditer(pattern, time_str)
        for match in matches:
            day, details = match.group(1), match.group(2)
            room = (re.search(r'\[(.*?)\]', details).group(1) if re.search(r'\[(.*?)\]', details) else '')
            periods = sorted([int(p) for p in re.findall(r'\d+', re.sub(r'\[.*?\]', '', details))])
            if periods: parsed.append({'day': day, 'periods': periods, 'room': room})
        return parsed

    df['parsed_time'] = df['강의시간/강의실'].apply(parse_time)
    
    # (요일, 교시) set 테이블 사전 빌드 (중복 체크 연산 최적화)
    def create_time_slots_set(parsed_time_list):
        slots = set()
        for time_info in parsed_time_list:
            for period in time_info['periods']:
                slots.add((time_info['day'], period))
        return slots
        
    df['time_slots_set'] = df['parsed_time'].apply(create_time_slots_set)
    return df

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
    time_display = x['강의시간/강의실'] if pd.notna(x['강의시간/강의실']) else "시간미지정"
    professor = x['교수명'] if pd.notna(x['교수명']) else "미정"
    
    if mode == 'selectbox':
        formatted_bunban = f"{x['분반']}반"
        base_str = f"[{x['학부(과)']}/{x['이수구분']}] {x['교과목명']} ({professor}, {formatted_bunban}, {x['학점']}학점) / {time_display}"
    else:
        base_str = f"[{x['이수구분']}] {x['교과목명']} ({professor}) / {time_display}"
        
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

# --- 앱 기본 실행 파트 ---
master_df = load_yonsei_data()

if 'my_courses' not in st.session_state: st.session_state.my_courses = []
if 'color_map' not in st.session_state: st.session_state.color_map = {}

# URL 공유 파라미터 파싱
if "courses" in st.query_params and not st.session_state.my_courses:
    try:
        courses_str = st.query_params.get("courses")
        if courses_str:
            shared_courses = []
            for item in courses_str.split(','):
                if '-' in item:
                    code, no = item.split('-')
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
    except Exception:
        st.error("공유된 URL의 형식이 올바르지 않습니다.")
        st.query_params.clear()

available_df = get_available_courses(master_df, st.session_state.my_courses)

# --- 필터 레이아웃 ---
st.subheader("1. 강좌 필터링 및 선택")
col1, col2, col3, col4 = st.columns(4)

with col1:
    dept_options = sorted(master_df['학부(과)'].unique().tolist())
    selected_depts = st.multiselect("학부(과) / 전공 선택", dept_options, placeholder="전체 학과 검색")

with col2:
    type_options = sorted(master_df['이수구분'].unique().tolist())
    selected_type = st.selectbox("이수구분", ["전체"] + type_options)

with col3:
    credit_options = sorted(master_df['학점'].unique().tolist())
    selected_credit = st.selectbox("학점", ["전체"] + [f"{c}학점" for c in credit_options])

with col4:
    day_filter = st.multiselect("원하는 요일", ['월', '화', '수', '목', '금', '토'])

# 필터링 로직 작동
filtered_df = available_df.copy()
if selected_depts:
    filtered_df = filtered_df[filtered_df['학부(과)'].isin(selected_depts)]
if selected_type != "전체":
    filtered_df = filtered_df[filtered_df['이수구분'] == selected_type]
if selected_credit != "전체":
    target_credit = int(selected_credit.replace("학점", ""))
    filtered_df = filtered_df[filtered_df['학점'] == target_credit]
if day_filter:
    filtered_df = filtered_df[filtered_df['time_slots_set'].apply(lambda slots: any(d in day_filter for d, p in slots))]

search_query = st.text_input("🔎 과목명 또는 교수명 검색", placeholder="예: 학습과학 혹은 이희승")
if search_query:
    q = search_query.lower()
    filtered_df = filtered_df[
        filtered_df['교과목명'].str.lower().str.contains(q, regex=False, na=False) |
        filtered_df['교수명'].str.lower().str.contains(q, regex=False, na=False)
    ]

st.write("---")

if filtered_df.empty:
    st.warning("선택한 조건에 일치하거나 현재 추가 가능한 강좌가 없습니다.")
else:
    st.info(f"**{len(filtered_df)}개**의 강좌를 찾았습니다.")
    
    selected_index = st.selectbox(
        "추가할 강좌 선택",
        options=filtered_df.index,
        format_func=lambda idx: format_course_string(filtered_df.loc[idx], mode='selectbox'),
        label_visibility="collapsed",
        placeholder="강좌를 선택하세요..."
    )
    
    if selected_index is not None:
        if st.button("내 시간표에 추가하기", use_container_width=True, type="primary"):
            add_course_to_timetable(filtered_df.loc[selected_index])

# --- 2. 시간표 렌더링 파트 ---
st.divider()
st.subheader("2. 나의 시간표 수강 현황")

if not st.session_state.my_courses:
    st.info("과목을 추가하면 실시간 시간표가 여기에 시각화됩니다.")
else:
    my_courses_df = master_df[master_df.set_index(['교과목코드', '분반']).index.isin(st.session_state.my_courses)]
    
    days_order = ['월', '화', '수', '목', '금', '토']
    days_to_display_set = set(['월', '화', '수', '목', '금'])
    for _, course in my_courses_df.iterrows():
        for t_info in course['parsed_time']:
            days_to_display_set.add(t_info['day'])
    days_to_display = [d for d in days_order if d in days_to_display_set]
    
    # 교시 범위 설정 (교육대학원 야간수업 고려하여 기본 1~9교시 세팅 후 자동 확장)
    all_periods = [p for _, c in my_courses_df.iterrows() for t in c['parsed_time'] for p in t['periods']]
    final_max_period = max(9, max(all_periods)) if all_periods else 9
    
    timetable_data = {}
    for p in range(1, final_max_period + 1):
        for d in days_to_display:
            timetable_data[(p, d)] = {"content": "", "color": "white", "span": 1, "is_visible": True}
            
    for _, course in my_courses_df.iterrows():
        if course['parsed_time']:
            color = st.session_state.color_map.get(course['교과목명'], "white")
            for t_info in course['parsed_time']:
                if t_info['day'] not in days_to_display: continue
                content = f"<b>{course['교과목명']}</b><br>{course['교수명']}<br>{t_info['room']}"
                periods = sorted(t_info['periods'])
                if not periods: continue
                
                start_period, block_len = periods[0], 1
                for i in range(1, len(periods)):
                    if periods[i] == periods[i-1] + 1:
                        block_len += 1
                    else:
                        if (start_period, t_info['day']) in timetable_data:
                            timetable_data[(start_period, t_info['day'])].update({"content": content, "color": color, "span": block_len})
                            for j in range(1, block_len):
                                timetable_data[(start_period + j, t_info['day'])]["is_visible"] = False
                        start_period, block_len = periods[i], 1
                if (start_period, t_info['day']) in timetable_data:
                    timetable_data[(start_period, t_info['day'])].update({"content": content, "color": color, "span": block_len})
                    for j in range(1, block_len):
                        timetable_data[(start_period + j, t_info['day'])]["is_visible"] = False

    day_col_width = 90 / len(days_to_display)
    table_html = f'<div id="timetable-to-capture"><table class="timetable"><tr><th width="10%">교시</th>'
    for d in days_to_display: table_html += f'<th width="{day_col_width}%">{d}</th>'
    table_html += '</tr>'
    
    # 시간 표시용 맵핑 (연대 교대원 특화 야간 시간 표기 필요 시 수정 가능)
    for p in range(1, final_max_period + 1):
        table_html += f'<tr><td>{p}교시</td>'
        for d in days_to_display:
            cell = timetable_data.get((p, d))
            if cell and cell["is_visible"]:
                table_html += f'<td rowspan="{cell["span"]}" style="background-color:{cell["color"]};">{cell["content"]}</td>'
        table_html += '</tr>'
        
    # 특수 형태 (시간 미지정 / 토요일 연구방법론 등) 처리 행
    untimed_courses = [c for _, c in my_courses_df.iterrows() if not c['parsed_time']]
    if untimed_courses:
        table_html += '<tr><td style="font-weight:bold;">시간 미지정</td>'
        untimed_content = "<br>".join([f"<b>{c['교과목명']}</b> ({c['교수명']}) / {c['강의시간/강의실']}" for c in untimed_courses])
        table_html += f'<td colspan="{len(days_to_display)}" style="text-align: left; padding: 8px; background-color: #f8f9fa;">{untimed_content}</td></tr>'
        
    table_html += "</table></div>"
    
    # HTML 및 Canvas 캡처 기능 연동
    button_html = """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <button id="download-btn-component" class="download-btn">시간표 이미지로 저장</button>
    <div id="status-message" style="margin-top:10px;font-size:14px"></div>
    <script>
        document.getElementById('download-btn-component').onclick = function() {
            const element = document.getElementById("timetable-to-capture");
            const statusDiv = document.getElementById('status-message');
            if (element) {
                statusDiv.innerText = '이미지 생성 중...'; statusDiv.style.color = 'blue';
                html2canvas(element, { scale: 3, useCORS: true, backgroundColor: '#ffffff' })
                .then(canvas => {
                    const link = document.createElement("a");
                    link.href = canvas.toDataURL("image/png");
                    link.download = "연세대-교육대학원-시간표.png";
                    document.body.appendChild(link); link.click(); document.body.removeChild(link);
                    statusDiv.innerText = '✅ 다운로드가 시작되었습니다.'; statusDiv.style.color = 'green';
                }).catch(err => { statusDiv.innerText = '❌ 오류: ' + err; statusDiv.style.color = 'red'; });
            }
        };
    </script>
    """
    
    combined_html = f"""
    <style>
    .timetable{{width:100%;border-collapse:collapse;table-layout:fixed;}}
    .timetable th,.timetable td{{border:1px solid #e0e0e0;text-align:center;vertical-align:middle;padding:4px;height:55px;font-size:.85em;word-break:keep-all}}
    .timetable th{{background-color:#f0f2f6;font-weight:700}}
    .download-btn{{display:inline-block;padding:10px 20px;background-color:#002c62;color:#fff;border-radius:5px;border:none;cursor:pointer;font-size:16px;margin-top:20px}}
    .download-btn:hover{{background-color:#001c40}}
    </style>
    {table_html} {button_html}
    """
    st.components.v1.html(combined_html, height=(final_max_period * 60 + 150))
    
    # 수강 목록 내역 계산 및 출력부
    st.write("---")
    list_col, action_col = st.columns([0.8, 0.2])
    
    with list_col:
        total_credits = my_courses_df['학점'].sum()
        st.markdown(f"#### 📝 선택한 강좌 내역 [총 {len(st.session_state.my_courses)}과목, **{total_credits}학점** 수강]")
        st.info("💡 시간표를 원격 공유하려면 브라우저 주소창의 URL 주소를 그대로 복사해 전달하세요.")
        
    with action_col:
        if st.button("전체 초기화", type="primary", use_container_width=True):
            st.session_state.my_courses = []
            st.session_state.color_map = {}
            st.query_params.clear()
            st.rerun()
            
    # 개별 제거 버튼 배치
    for idx, (code, no) in enumerate(st.session_state.my_courses):
        course_row = master_df[(master_df['교과목코드'] == code) & (master_df['분반'] == no)].iloc[0]
        c_col, b_col = st.columns([0.88, 0.12])
        with c_col:
            st.markdown(f"• **{course_row['교과목명']}** ({course_row['교수명']}) | {course_row['학부(과)']} [{code}-{no}]")
        with b_col:
            if st.button("제거", key=f"del-{code}-{no}-{idx}", use_container_width=True):
                st.session_state.my_courses.pop(idx)
                if st.session_state.my_courses:
                    st.query_params["courses"] = ",".join([f"{c}-{n}" for c, n in st.session_state.my_courses])
                else:
                    st.query_params.clear()
                st.rerun()
