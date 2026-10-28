import os
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from extract_offers_ai import extract_offers_from_pages
from extract_pdf import extract_pdf_pages
from save_offers import save_offers_from_preview

st.set_page_config(page_title='Espace Analyste', page_icon='🧩', layout='wide')
st.title('Espace Analyste')
st.caption('Import, extraction IA et enregistrement des catalogues.')

with st.form('catalogue_form'):
    uploaded_file = st.file_uploader('Téléverser un catalogue PDF', type=['pdf'])
    operator_name = st.selectbox('Opérateur', ['Maroc Telecom', 'Orange', 'inwi'])
    segment = st.selectbox('Segment', ['B2C'])
    edition = st.text_input('Édition', value='')
    url_source = st.text_input('URL source', value='')
    submitted = st.form_submit_button('Extraire les offres')

if not uploaded_file:
    st.info('Sélectionnez un PDF pour lancer l’extraction des offres.')
    st.stop()

with tempfile.TemporaryDirectory() as tmp_dir:
    temp_pdf = Path(tmp_dir) / uploaded_file.name
    temp_pdf.write_bytes(uploaded_file.getvalue())
    pages = extract_pdf_pages(temp_pdf)
    offers = extract_offers_from_pages(pages, operator_name=operator_name)

    if not offers:
        st.warning('Aucune offre n’a été détectée. Vérifiez le texte du PDF ou lancez une nouvelle extraction.')
        st.stop()

    st.subheader('Aperçu des offres détectées')
    preview_df = pd.DataFrame(offers)
    edited_df = st.data_editor(preview_df, use_container_width=True, num_rows='dynamic')

    if st.button('Enregistrer les offres en base'):
        result = save_offers_from_preview(
            edited_df.to_dict(orient='records'),
            uploaded_file.name,
            operator_name,
            segment=segment,
            edition=edition or None,
            url_source=url_source or None,
        )
        if result['saved_count'] > 0:
            st.success(f'{result["saved_count"]} offres enregistrées avec est_validee = 0.')
        else:
            st.info('Aucune nouvelle offre n’a été ajoutée (fichier déjà traité ou aucune offre valide).')
