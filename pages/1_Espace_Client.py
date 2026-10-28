import pandas as pd
import streamlit as st

from analyse_offers import compute_missed_tiers, create_gap_chart, create_price_chart, create_speed_chart, get_market_dataframe

st.set_page_config(page_title='Espace Client', page_icon='📊', layout='wide')

st.title('Espace Client')
st.caption('Benchmark Fibre B2C - offres validées uniquement')

mode = st.sidebar.radio('Type de fibre', ['Avec TV', 'Fibre seule'], index=0, horizontal=True)
fibre_only = mode == 'Fibre seule'
raw_data = get_market_dataframe(operator_name=None, fibre_only=fibre_only)
if raw_data.empty:
    fallback_mode = not fibre_only
    raw_data = get_market_dataframe(operator_name=None, fibre_only=fallback_mode)
    if raw_data.empty:
        st.warning('Aucune offre validée n’est disponible pour le moment. Vérifiez la base SQL Server et la vue dbo.v_OffresValidees.')
        st.stop()
    st.info('Aucune offre dans le filtre sélectionné. Le benchmark a été basculé sur le mode disponible.')
    fibre_only = fallback_mode

operators = sorted(raw_data['operateur'].dropna().unique().tolist())
selected_operator = st.sidebar.selectbox('Opérateur client', operators)
filtered = get_market_dataframe(operator_name=selected_operator, fibre_only=fibre_only)

if filtered.empty:
    st.warning(f'Aucune offre correspondant à {selected_operator} dans ce filtre n’a été trouvée.')
    st.stop()

st.subheader('Tableau comparatif')
cols = [
    'operateur', 'nom_offre', 'debit_mbps', 'prix_mensuel_ttc', 'engagement_mois',
    'frais_installation_ttc', 'appels_inclus', 'conditions_offre',
    'prix_par_100_mbps', 'ecart_a_median_market', 'rang_operateur'
]
visible = filtered[cols].copy()
visible = visible.rename(columns={
    'operateur': 'Opérateur',
    'nom_offre': 'Offre',
    'debit_mbps': 'Débit (Mbps)',
    'prix_mensuel_ttc': 'Prix mensuel TTC (DH)',
    'engagement_mois': 'Engagement (mois)',
    'frais_installation_ttc': 'Frais installation TTC (DH)',
    'appels_inclus': 'Appels inclus',
    'conditions_offre': 'Conditions',
    'prix_par_100_mbps': 'Prix / 100Mbps',
    'ecart_a_median_market': 'Écart médiane marché (DH)',
    'rang_operateur': 'Rang du client'
})

st.dataframe(visible, use_container_width=True, hide_index=True)

st.subheader('Indicateurs calculés')
col1, col2, col3 = st.columns(3)
with col1:
    st.metric('Prix moyen', f"{filtered['prix_mensuel_ttc'].mean():,.2f} DH")
with col2:
    st.metric('Débit moyen', f"{filtered['debit_mbps'].mean():,.0f} Mbps")
with col3:
    st.metric('Médiane du marché', f"{filtered['prix_median_market'].median():,.2f} DH")

st.write('Paliers de débit non couverts :')
missing_tiers = compute_missed_tiers(selected_operator, fibre_only)
if missing_tiers:
    st.write(', '.join(str(item) for item in missing_tiers))
else:
    st.write('Aucun palier de débit manquant pour cet opérateur dans le filtre sélectionné.')

chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    price_chart = create_price_chart(filtered)
    if price_chart is not None:
        st.plotly_chart(price_chart, use_container_width=True)
with chart_col2:
    speed_chart = create_speed_chart(filtered)
    if speed_chart is not None:
        st.plotly_chart(speed_chart, use_container_width=True)

st.plotly_chart(create_gap_chart(filtered), use_container_width=True)
