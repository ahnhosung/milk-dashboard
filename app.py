import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 웹 페이지의 탭 이름과 기본 레이아웃을 넓게(wide) 설정합니다.
st.set_page_config(page_title="우유 소비 대시보드", layout="wide")

# 1. 아까 주피터에서 성공했던 완벽한 전처리 코드 그대로 가져오기
@st.cache_data # 이 마법의 주문을 달아두면, 웹을 새로고침해도 매번 엑셀을 다시 읽지 않아 속도가 엄청 빠릅니다.
def load_data():
    # 엑셀 불러오기 및 껍데기 날리기
    df_raw = pd.read_excel('농림축산부_우유_생산_소비현황.xlsx', sheet_name='유제품별 생산소비실적', header=None)
    df_raw = df_raw.dropna(axis=0, how='all').dropna(axis=1, how='all').reset_index(drop=True)
    
    # 빈칸 채우기
    df_raw.iloc[0] = df_raw.iloc[0].ffill()
    df_raw.iloc[:, 0] = df_raw.iloc[:, 0].ffill()
    df_raw = df_raw.drop(0).reset_index(drop=True)
    df_raw.iloc[:, 1] = df_raw.iloc[:, 1].fillna(df_raw.iloc[:, 0])
    
    # 컬럼명 1줄로 합치기
    new_columns = [f"{year}_{type_}" for year, type_ in zip(df_raw.iloc[0], df_raw.iloc[1])]
    df_raw.columns = new_columns
    df_raw = df_raw.drop([0, 1]).reset_index(drop=True)
    
    # 컬럼명 정리 및 중복 유령 컬럼 제거
    cols = list(df_raw.columns)
    cols[0] = '대분류'
    cols[1] = '소분류'
    df_raw.columns = cols
    df_raw = df_raw.loc[:, ~df_raw.columns.duplicated()]
    
    # 연도 오름차순 정렬
    cols = list(df_raw.columns)
    sorted_cols = cols[:2] + sorted(cols[2:])
    df_raw = df_raw[sorted_cols]
    
    return df_raw

# 전처리된 데이터 불러오기
df = load_data()

# 화면 타이틀
st.title("🥛 국내 우유 생산 및 소비 트렌드 대시보드")

# 1. 원본 데이터 표 (공간을 덜 차지하도록 접었다 펼 수 있는 Expander 기능 사용)
with st.expander("데이터프레임 원본 확인하기 (클릭해서 펼치기)"):
    st.dataframe(df)

# --- (기존의 load_data() 함수 및 df, st.expander 코드는 그대로 둡니다) ---

# 2. 본격적인 대시보드 레이아웃 시작 (화면을 좌우 2칸으로 쪼개기)
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 품목별 연도별 소비량 추이")
    
    # [핵심 1] 셀렉트박스 추가: 사용자가 원하는 소분류 품목을 직접 고를 수 있게 합니다.
    product_list = df['소분류'].unique()
    selected_product = st.selectbox("조회할 품목을 선택하세요:", product_list, index=0)

    # 선택된 품목으로 데이터 필터링
    filtered_data = df[df['소분류'] == selected_product]
    consume_cols = [col for col in df.columns if '국내소비' in col]
    years = [col[:4] for col in consume_cols]
    values = filtered_data[consume_cols].iloc[0].values

    # 그래프 1 (꺾은선) 그리기
    fig1, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(years, values, marker='o', color='dodgerblue', linewidth=2)
    ax1.set_title(f'{selected_product} 연도별 국내 소비량 (2001~2023)', fontweight='bold')
    ax1.set_xlabel('연도')
    ax1.set_ylabel('소비량 (톤)')
    plt.xticks(rotation=45) 
    ax1.grid(True, linestyle='--', alpha=0.6)
    
    st.pyplot(fig1)

with col2:
    # 1. '국내소비'가 포함된 컬럼만 모아서 가장 마지막(최신) 연도 컬럼을 자동으로 찾습니다.
    consume_cols = [col for col in df.columns if '국내소비' in col]
    latest_consume_col = sorted(consume_cols)[-1] # 예: '2022_국내소비'가 자동으로 뽑힘
    latest_year = latest_consume_col[:4] # '2022' 글자만 추출
    
    st.subheader(f"🍩 {latest_year}년 유제품 소비 비중")
    st.write(f"공공데이터 포털 최신 집계({latest_year}년) 기준입니다.")
    
    # 2. 에러가 났던 하드코딩 부분을 동적 변수(latest_consume_col)로 완벽하게 교체합니다.
    df[latest_consume_col] = pd.to_numeric(df[latest_consume_col], errors='coerce')
    df_latest = df[['소분류', latest_consume_col]].dropna().sort_values(by=latest_consume_col, ascending=False)
    
    # 파이 차트 그리기
    top_5 = df_latest.head(5)
    
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    ax2.pie(top_5[latest_consume_col], labels=top_5['소분류'], autopct='%1.1f%%', startangle=90, colors=plt.cm.Set3.colors)
    ax2.set_title(f'{latest_year}년 상위 5개 품목 소비 비중', fontweight='bold')
    
    st.pyplot(fig2)


# --- (기존의 col1, col2 대시보드 코드는 그대로 둡니다) ---

# 3. 화면을 가로지르는 구분선 추가
st.markdown("---")
st.subheader("⚖️ 백색시유 수급 균형 분석 (국내 생산 vs 소비)")
st.write("우리나라의 우유 생산량이 소비량을 얼마나 뒷받침하고 있는지, 그 '격차'를 확인합니다.")

# [핵심] '백색시유' 데이터만 쏙 뽑아내기
white_milk = df[(df['대분류'] == '백색시유') & (df['소분류'] == '백색시유')]

# [해결책] 생산량과 소비량 데이터가 '모두' 존재하는 연도(교집합)만 찾아냅니다.
prod_years = set([col[:4] for col in df.columns if '국내생산' in col])
cons_years = set([col[:4] for col in df.columns if '국내소비' in col])

# 두 데이터가 모두 있는 연도만 추려서 오름차순으로 예쁘게 정렬합니다. (2009, 2010...)
valid_years = sorted(list(prod_years & cons_years))

prod_values = []
cons_values = []

# 안전하게 교집합 연도(valid_years)만 순회하며 데이터를 뽑습니다.
for y in valid_years:
    p_val = pd.to_numeric(white_milk[f'{y}_국내생산'].iloc[0], errors='coerce')
    c_val = pd.to_numeric(white_milk[f'{y}_국내소비'].iloc[0], errors='coerce')
    prod_values.append(p_val)
    cons_values.append(c_val)

# 그래프 3 (생산 vs 소비 겹쳐 그리기) 세팅
fig3, ax3 = plt.subplots(figsize=(12, 5))

# 생산량은 파란색, 소비량은 빨간색으로 그립니다.
ax3.plot(valid_years, prod_values, marker='o', color='dodgerblue', linewidth=2, label='국내 생산량')
ax3.plot(valid_years, cons_values, marker='s', color='tomato', linewidth=2, label='국내 소비량')

# 🔥 [포트폴리오 필살기] 두 선 사이의 공간(수급 격차)을 연한 회색으로 칠해줍니다.
ax3.fill_between(valid_years, prod_values, cons_values, color='gray', alpha=0.15, label='수급 격차 (부족분)')

# 제목에도 하드코딩 대신 동적으로 추출한 연도를 넣어줍니다.
ax3.set_title(f'백색시유 생산량 및 소비량 추이 ({valid_years[0]}~{valid_years[-1]})', fontweight='bold')
ax3.set_xlabel('연도')
ax3.set_ylabel('수량 (톤)')
plt.xticks(rotation=45)
ax3.grid(True, linestyle='--', alpha=0.6)
ax3.legend()

# 완성된 거대한 분석 그래프를 화면에 출력!
st.pyplot(fig3)