import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import json
import os

# 페이지 설정
st.set_page_config(
    page_title="자동차 부품 단가 계산기",
    page_icon="🚗",
    layout="wide"
)

# CSS 스타일 적용
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    .comparison-header {
        background-color: #f1f8ff;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

def load_saved_results():
    if os.path.exists('calculation_history.json'):
        with open('calculation_history.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_calculation(scenario_name, inputs, results):
    history = load_saved_results()
    calculation = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'scenario_name': scenario_name,
        'inputs': inputs,
        'results': results
    }
    history.append(calculation)
    with open('calculation_history.json', 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def calculate_price_with_cr(base_price, cr, cr_years):
    cr_rate = 1
    for _ in range(cr_years):
        cr_rate *= (1 - cr/100)
    return base_price / cr_rate

def calculate_price_with_bl(price, bl):
    return price / (1 - bl/100)

def calculate_finance_cost(price, annual_interest, payment_before, payment_after):
    daily_interest = annual_interest / 365 / 100
    delay_days = payment_after - payment_before
    return price * daily_interest * delay_days

def calculate_yearly_prices(initial_price, cr, cr_years):
    prices = []
    current_price = initial_price
    for year in range(1, cr_years + 1):
        prices.append({
            'year': year,
            'price': current_price,
            'reduction': cr
        })
        current_price *= (1 - cr/100)
    return prices

def create_comparison_chart(scenario1, scenario2):
    # 연도별 단가 비교 그래프
    yearly_prices1 = pd.DataFrame(scenario1['results']['yearly_prices'])
    yearly_prices2 = pd.DataFrame(scenario2['results']['yearly_prices'])
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('연도별 단가 비교', '단가 상승 요인 분석'),
        vertical_spacing=0.15
    )
    
    # 연도별 단가 선 그래프
    fig.add_trace(
        go.Scatter(x=yearly_prices1['year'], y=yearly_prices1['price'],
                  name=f"시나리오 1: {scenario1['name']}", line=dict(color='#1f77b4')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=yearly_prices2['year'], y=yearly_prices2['price'],
                  name=f"시나리오 2: {scenario2['name']}", line=dict(color='#ff7f0e')),
        row=1, col=1
    )
    
    # 상승 요인 분석 막대 그래프
    factors = ['CR 상승', 'BL 상승', '금융비용']
    values1 = [
        scenario1['results']['base_with_cr'] - scenario1['inputs']['base_price'],
        scenario1['results']['base_with_bl'] - scenario1['results']['base_with_cr'],
        scenario1['results']['piece_finance_cost']
    ]
    values2 = [
        scenario2['results']['base_with_cr'] - scenario2['inputs']['base_price'],
        scenario2['results']['base_with_bl'] - scenario2['results']['base_with_cr'],
        scenario2['results']['piece_finance_cost']
    ]
    
    fig.add_trace(
        go.Bar(x=factors, y=values1, name=f"시나리오 1: {scenario1['name']}", marker_color='#1f77b4'),
        row=2, col=1
    )
    fig.add_trace(
        go.Bar(x=factors, y=values2, name=f"시나리오 2: {scenario2['name']}", marker_color='#ff7f0e'),
        row=2, col=1
    )
    
    fig.update_layout(
        height=800,
        showlegend=True,
        template='plotly_white',
        yaxis_title='단가 (원)',
        yaxis2_title='금액 (원)'
    )
    
    return fig

def input_section(key_suffix):
    inputs = {}
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            inputs['base_price'] = st.number_input('기본 단가 (원)', value=10000, key=f'base_price_{key_suffix}')
            inputs['cr'] = st.number_input('CR (연간 단가 인하율 %)', value=3.0, key=f'cr_{key_suffix}')
            inputs['cr_years'] = st.number_input('CR 적용 연수', value=4, key=f'cr_years_{key_suffix}')
            inputs['bl'] = st.number_input('BL (%)', value=1.0, key=f'bl_{key_suffix}')
        with col2:
            inputs['payment_before'] = st.number_input('대금지급 시작일 (days)', value=60, key=f'payment_before_{key_suffix}')
            inputs['payment_after'] = st.number_input('대금지급 종료일 (days)', value=120, key=f'payment_after_{key_suffix}')
            inputs['annual_interest'] = st.number_input('연 이자율 (%)', value=5.0, key=f'annual_interest_{key_suffix}')
    return inputs

def calculate_results(inputs):
    price_with_cr = calculate_price_with_cr(inputs['base_price'], inputs['cr'], inputs['cr_years'])
    price_with_bl = calculate_price_with_bl(price_with_cr, inputs['bl'])
    finance_cost = calculate_finance_cost(price_with_bl, inputs['annual_interest'], 
                                       inputs['payment_before'], inputs['payment_after'])
    final_price = price_with_bl + finance_cost
    yearly_prices = calculate_yearly_prices(final_price, inputs['cr'], inputs['cr_years'])
    
    return {
        'base_with_cr': price_with_cr,
        'base_with_bl': price_with_bl,
        'piece_finance_cost': finance_cost,
        'final_price': final_price,
        'yearly_prices': yearly_prices
    }

def display_metrics(scenario1, scenario2):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### 시나리오 1: {scenario1['name']}")
        results1 = scenario1['results']
        metrics1 = st.container()
        with metrics1:
            subcol1, subcol2 = st.columns(2)
            with subcol1:
                st.metric("기본 단가", f"{scenario1['inputs']['base_price']:,.0f}원")
                st.metric("CR 반영 단가", f"{results1['base_with_cr']:,.0f}원")
                st.metric("BL 반영 단가", f"{results1['base_with_bl']:,.0f}원")
            with subcol2:
                st.metric("개당 금융비용", f"{results1['piece_finance_cost']:,.0f}원")
                st.metric("최종 필요 단가", f"{results1['final_price']:,.0f}원", 
                         delta=f"{results1['final_price'] - scenario1['inputs']['base_price']:,.0f}원")
    
    with col2:
        st.markdown(f"### 시나리오 2: {scenario2['name']}")
        results2 = scenario2['results']
        metrics2 = st.container()
        with metrics2:
            subcol1, subcol2 = st.columns(2)
            with subcol1:
                st.metric("기본 단가", f"{scenario2['inputs']['base_price']:,.0f}원")
                st.metric("CR 반영 단가", f"{results2['base_with_cr']:,.0f}원")
                st.metric("BL 반영 단가", f"{results2['base_with_bl']:,.0f}원")
            with subcol2:
                st.metric("개당 금융비용", f"{results2['piece_finance_cost']:,.0f}원")
                st.metric("최종 필요 단가", f"{results2['final_price']:,.0f}원",
                         delta=f"{results2['final_price'] - scenario2['inputs']['base_price']:,.0f}원")

def main():
    st.title('🚗 자동차 부품 단가 계산기')
    st.markdown("---")
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["📊 시나리오 비교", "📝 상세 분석", "📚 저장된 결과"])
    
    with tab1:
        # 시나리오 이름 입력
        col1, col2 = st.columns(2)
        with col1:
            scenario1_name = st.text_input("시나리오 1 이름", value="기본 시나리오")
        with col2:
            scenario2_name = st.text_input("시나리오 2 이름", value="대안 시나리오")
        
        # 입력 섹션
        st.markdown("### 시나리오 1 입력")
        inputs1 = input_section('scenario1')
        st.markdown("### 시나리오 2 입력")
        inputs2 = input_section('scenario2')
        
        if st.button('계산하기', key='calculate_comparison'):
            # 결과 계산
            results1 = calculate_results(inputs1)
            results2 = calculate_results(inputs2)
            
            # 세션 스테이트에 저장
            st.session_state.scenario1 = {
                'name': scenario1_name,
                'inputs': inputs1,
                'results': results1
            }
            st.session_state.scenario2 = {
                'name': scenario2_name,
                'inputs': inputs2,
                'results': results2
            }
            
            # 결과 표시
            st.markdown("## 비교 결과")
            display_metrics(st.session_state.scenario1, st.session_state.scenario2)
            
            # 차트 표시
            st.markdown("### 📈 시각화")
            fig = create_comparison_chart(st.session_state.scenario1, st.session_state.scenario2)
            st.plotly_chart(fig, use_container_width=True)
            
            # 저장 버튼
            if st.button('결과 저장하기'):
                save_calculation(scenario1_name, inputs1, results1)
                save_calculation(scenario2_name, inputs2, results2)
                st.success('두 시나리오의 계산 결과가 저장되었습니다!')
    
    with tab2:
        if 'scenario1' in st.session_state and 'scenario2' in st.session_state:
            st.markdown("## 상세 분석")
            
            # 연도별 단가 예측 테이블
            st.markdown("### 📅 연도별 단가 예측")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"#### {st.session_state.scenario1['name']}")
                yearly_df1 = pd.DataFrame(st.session_state.scenario1['results']['yearly_prices'])
                st.dataframe(yearly_df1.style.format({
                    'price': '{:,.0f}원',
                    'reduction': '{:.1f}%'
                }))
            
            with col2:
                st.markdown(f"#### {st.session_state.scenario2['name']}")
                yearly_df2 = pd.DataFrame(st.session_state.scenario2['results']['yearly_prices'])
                st.dataframe(yearly_df2.style.format({
                    'price': '{:,.0f}원',
                    'reduction': '{:.1f}%'
                }))
            
            # 상승 요인 분석
            st.markdown("### 📈 단가 상승 요인 분석")
            col1, col2 = st.columns(2)
            
            def create_analysis_df(scenario):
                results = scenario['results']
                inputs = scenario['inputs']
                cr_increase = results['base_with_cr'] - inputs['base_price']
                bl_increase = results['base_with_bl'] - results['base_with_cr']
                total_increase = results['final_price'] - inputs['base_price']
                
                return pd.DataFrame({
                    '상승 요인': ['CR로 인한 상승', 'BL로 인한 상승', '금융비용', '총 상승분'],
                    '금액': [cr_increase, bl_increase, results['piece_finance_cost'], total_increase]
                })
            
            with col1:
                st.markdown(f"#### {st.session_state.scenario1['name']}")
                analysis_df1 = create_analysis_df(st.session_state.scenario1)
                st.dataframe(analysis_df1.style.format({
                    '금액': '{:+,.0f}원'
                }))
            
            with col2:
                st.markdown(f"#### {st.session_state.scenario2['name']}")
                analysis_df2 = create_analysis_df(st.session_state.scenario2)
                st.dataframe(analysis_df2.style.format({
                    '금액': '{:+,.0f}원'
                }))
        else:
            st.info('먼저 시나리오 비교 탭에서 계산을 진행해주세요.')
    
    with tab3:
        st