from __future__ import annotations

import pandas as pd
import plotly.express as px

from db_connection import read_valid_offers


def _prepare_offers_frame(raw_rows):
    if not raw_rows:
        return pd.DataFrame()

    df = pd.DataFrame(raw_rows)
    numeric_cols = [
        'debit_mbps',
        'prix_mensuel_ttc',
        'engagement_mois',
        'frais_installation_ttc',
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df['debit_tier'] = pd.cut(
        df['debit_mbps'],
        bins=[0, 50, 100, 200, 500, 1000, float('inf')],
        labels=['<= 50', '51-100', '101-200', '201-500', '501-1000', '> 1000'],
        right=False,
    )
    df['prix_par_100_mbps'] = df.apply(
        lambda row: (row['prix_mensuel_ttc'] / row['debit_mbps']) * 100 if pd.notna(row['debit_mbps']) and row['debit_mbps'] else None,
        axis=1,
    )
    df['est_avec_tv'] = df['nom_offre'].fillna('').str.contains('TV', case=False, na=False)
    return df


def get_market_dataframe(operator_name: str | None = None, fibre_only: bool = True):
    base_columns = [
        'id_offre', 'operateur', 'nom_offre', 'segment', 'technologie', 'debit_mbps', 'prix_mensuel_ttc',
        'engagement_mois', 'frais_installation_ttc', 'appels_inclus', 'conditions_offre', 'nom_fichier',
        'edition', 'url_source', 'page_source', 'extrait_source', 'debit_tier', 'prix_par_100_mbps',
        'est_avec_tv', 'prix_median_market', 'ecart_a_median_market', 'ecart_pct_market', 'rang_operateur'
    ]

    offers = read_valid_offers()
    df = _prepare_offers_frame(offers)
    if df.empty:
        return pd.DataFrame(columns=base_columns)

    if operator_name:
        df = df[df['operateur'] == operator_name].copy()

    df = df[df['est_avec_tv'] == (not fibre_only)].copy() if not df.empty else df

    market_tier_medians = _prepare_offers_frame(read_valid_offers())
    if market_tier_medians.empty:
        return df.reindex(columns=base_columns)

    market_tier_medians = market_tier_medians[market_tier_medians['est_avec_tv'] == (not fibre_only)].copy()
    median_prices = market_tier_medians.groupby('debit_tier', observed=False)['prix_mensuel_ttc'].median().rename('prix_median_market')

    if df.empty:
        return df.reindex(columns=base_columns)

    df = df.merge(median_prices, on='debit_tier', how='left')
    df['ecart_a_median_market'] = df['prix_mensuel_ttc'] - df['prix_median_market']
    df['ecart_pct_market'] = df.apply(
        lambda row: (row['ecart_a_median_market'] / row['prix_median_market']) * 100 if pd.notna(row['prix_median_market']) and row['prix_median_market'] else None,
        axis=1,
    )
    df['rang_operateur'] = df.groupby('debit_tier')['prix_mensuel_ttc'].rank(method='first', ascending=True)
    return df.reindex(columns=base_columns).sort_values(['debit_tier', 'prix_mensuel_ttc'])


def compute_missed_tiers(operator_name: str | None = None, fibre_only: bool = True):
    raw = read_valid_offers()
    df = _prepare_offers_frame(raw)
    if df.empty:
        return []

    if fibre_only:
        df = df[~df['est_avec_tv']].copy()
    else:
        df = df[df['est_avec_tv']].copy()

    if operator_name:
        selected = df[df['operateur'] == operator_name].copy()
    else:
        selected = df.copy()

    market_tiers = set(df['debit_tier'].dropna().unique())
    selected_tiers = set(selected['debit_tier'].dropna().unique())
    return sorted(market_tiers - selected_tiers, key=lambda item: str(item))


def create_price_chart(df):
    if df.empty:
        return None
    return px.bar(
        df,
        x='nom_offre',
        y='prix_mensuel_ttc',
        color='operateur',
        title='Prix mensuel TTC par offre',
        labels={'prix_mensuel_ttc': 'Prix mensuel TTC (DH)', 'nom_offre': 'Offre'},
    )


def create_speed_chart(df):
    if df.empty:
        return None
    return px.scatter(
        df,
        x='debit_mbps',
        y='prix_par_100_mbps',
        color='operateur',
        size='prix_mensuel_ttc',
        hover_name='nom_offre',
        title='Prix par 100 Mbps',
        labels={'debit_mbps': 'Débit (Mbps)', 'prix_par_100_mbps': 'Prix / 100 Mbps (DH)'}
    )


def create_gap_chart(df):
    if df.empty:
        return None
    return px.bar(
        df,
        x='nom_offre',
        y='ecart_a_median_market',
        color='operateur',
        title='Écart au prix médian du marché',
        labels={'ecart_a_median_market': 'Écart (DH)', 'nom_offre': 'Offre'}
    )
