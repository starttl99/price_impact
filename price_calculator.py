import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

def load_saved_results():
    """저장된 결과를 불러오는 함수"""
    if os.path.exists('calculation_history.json'):
        with open('calculation_history.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_calculation(inputs, results):
    """계산 결과를 저장하는 함수"""
    history = load_saved_results()
    
    calculation = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'inputs': inputs,
        'results': results
    }
    
    history.append(calculation)
    
    with open('calculation_history.json', 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def calculate_price_with_cr(base_price, cr, cr_years):
    """CR 적용된 최종 단가 계산"""
    cr_rate = 1
    for _ in range(cr_years):
        cr_rate *= (1 - cr/100)
    return base_price / cr_rate

def calculate_price_with_bl(price, bl):
    """BL 적용"""
    return price / (1 - bl/100)

def calculate_finance_cost(price, annual_interest, payment_before, payment_after):
    """금융비용 계산"""
    daily_interest = annual_interest / 365 / 100
    delay_days = payment_after - payment_before
    return price * daily_interest * delay_days

def calculate_yearly_prices(initial_price, cr, cr_years):
    """연도별 단가 계산"""
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

def main():
    st.title('자동차 부품 단가 계산기')
    
    # 사이드바에 입력 폼 배치
    with st.sidebar:
        st.header('기본 정보 입력')
        base_price = st.number_input('기본 단가 (원)', value=10000)
        cr = st.number_input('CR (연간 단가 인하율 %)', value=3.0)
        cr_years = st.number_input('CR 적용 연수', value=4)
        bl = st.number_input('BL (%)', value=1.0)
        payment_before = st.number_input('대금지급 시작일 (days)', value=60)
        payment_after = st.number_input('대금지급 종료일 (days)', value=120)
        annual_interest = st.number_input('연 이자율 (%)', value=5.0)

    # 계산 버튼
    if st.sidebar.button('계산하기'):
        # 1. CR 영향 계산
        price_with_cr = calculate_price_with_cr(base_price, cr, cr_years)
        
        # 2. BL 영향 계산
        price_with_bl = calculate_price_with_bl(price_with_cr, bl)
        
        # 3. 금융비용 계산
        finance_cost = calculate_finance_cost(price_with_bl, annual_interest, payment_before, payment_after)
        final_price = price_with_bl + finance_cost
        
        # 연도별 단가 계산
        yearly_prices = calculate_yearly_prices(final_price, cr, cr_years)
        
        # 결과를 세션 스테이트에 저장
        st.session_state.results = {
            'base_with_cr': price_with_cr,
            'base_with_bl': price_with_bl,
            'piece_finance_cost': finance_cost,
            'final_price': final_price,
            'yearly_prices': yearly_prices
        }
        
        # 입력값도 저장
        st.session_state.inputs = {
            'base_price': base_price,
            'cr': cr,
            'cr_years': cr_years,
            'bl': bl,
            'payment_before': payment_before,
            'payment_after': payment_after,
            'annual_interest': annual_interest
        }

    # 결과 표시
    if 'results' in st.session_state:
        results = st.session_state.results
        
        # 메인 결과
        st.header('계산 결과')
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric('기본 단가', f"{st.session_state.inputs['base_price']:,.0f}원")
            st.metric('CR 반영 단가', f"{results['base_with_cr']:,.0f}원")
            st.metric('BL 반영 단가', f"{results['base_with_bl']:,.0f}원")
        
        with col2:
            st.metric('개당 금융비용', f"{results['piece_finance_cost']:,.0f}원")
            st.metric('최종 필요 단가', f"{results['final_price']:,.0f}원")
        
        # 연도별 단가 예측
        st.subheader('연도별 단가 예측')
        yearly_df = pd.DataFrame(results['yearly_prices'])
        yearly_df['price'] = yearly_df['price'].round(2)
        st.dataframe(yearly_df.style.format({
            'price': '{:,.0f}원',
            'reduction': '{:.1f}%'
        }))
        
        # 단가 상승 요인 분석
        st.subheader('단가 상승 요인 분석')
        cr_increase = results['base_with_cr'] - st.session_state.inputs['base_price']
        bl_increase = results['base_with_bl'] - results['base_with_cr']
        total_increase = results['final_price'] - st.session_state.inputs['base_price']
        
        analysis_df = pd.DataFrame({
            '상승 요인': ['CR로 인한 상승', 'BL로 인한 상승', '금융비용', '총 상승분'],
            '금액': [cr_increase, bl_increase, results['piece_finance_cost'], total_increase]
        })
        st.dataframe(analysis_df.style.format({
            '금액': '{:+,.0f}원'
        }))
        
        # 결과 저장 버튼
        if st.button('결과 저장하기'):
            save_calculation(st.session_state.inputs, results)
            st.success('계산 결과가 저장되었습니다!')
        
        # 저장된 결과 보기
        if st.button('저장된 결과 보기'):
            saved_results = load_saved_results()
            if saved_results:
                st.subheader('저장된 계산 기록')
                for idx, calc in enumerate(saved_results, 1):
                    with st.expander(f"계산 #{idx} - {calc['timestamp']}"):
                        st.json(calc)
            else:
                st.info('저장된 계산 결과가 없습니다.')

if __name__ == '__main__':
    main()