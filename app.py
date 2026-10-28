import streamlit as st

st.set_page_config(page_title='Market Insight AI', page_icon='📊', layout='wide')

st.title('Market Insight AI')
st.caption('MVP d’aide au benchmark des offres fibre B2C.')

st.write('Choisissez l’espace souhaité :')
st.page_link('pages/1_Espace_Client.py', label='➡️ Espace Client')
st.page_link('pages/2_Espace_Analyste.py', label='➡️ Espace Analyste')
