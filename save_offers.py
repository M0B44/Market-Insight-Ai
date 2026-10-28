from __future__ import annotations

from typing import Any

from db_connection import get_connection
from extract_offers_ai import extract_offers_from_pages
from extract_pdf import extract_pdf_pages


def ensure_operator(cursor, operator_name: str) -> int:
    cursor.execute('SELECT id_operateur FROM dbo.Operateurs WHERE nom = ?', (operator_name,))
    row = cursor.fetchone()
    if row:
        return int(row[0])

    cursor.execute('INSERT INTO dbo.Operateurs (nom) VALUES (?)', (operator_name,))
    cursor.execute('SELECT CAST(@@IDENTITY AS int) AS id_operateur')
    return int(cursor.fetchone()[0])


def ensure_catalogue(cursor, operator_id: int, nom_fichier: str, edition: str | None = None, segment: str = 'B2C', url_source: str | None = None) -> int:
    cursor.execute('SELECT id_catalogue FROM dbo.Catalogues WHERE nom_fichier = ?', (nom_fichier,))
    row = cursor.fetchone()
    if row:
        return int(row[0])

    cursor.execute(
        'INSERT INTO dbo.Catalogues (id_operateur, nom_fichier, edition, segment, url_source) VALUES (?, ?, ?, ?, ?)',
        (operator_id, nom_fichier, edition, segment, url_source),
    )
    cursor.execute('SELECT CAST(@@IDENTITY AS int) AS id_catalogue')
    return int(cursor.fetchone()[0])


def save_offers_for_catalogue(pdf_path: str, operator_name: str, segment: str = 'B2C', edition: str | None = None, url_source: str | None = None) -> dict[str, Any]:
    pages = extract_pdf_pages(pdf_path)
    offers = extract_offers_from_pages(pages, operator_name=operator_name)
    if not offers:
        return {'catalogue': pdf_path, 'saved_count': 0, 'already_exists': False, 'offers': []}

    with get_connection() as conn:
        cursor = conn.cursor()
        operator_id = ensure_operator(cursor, operator_name)
        catalogue_name = pdf_path.rsplit('/', 1)[-1].rsplit('\\', 1)[-1]
        catalogue_id = ensure_catalogue(cursor, operator_id, catalogue_name, edition, segment, url_source)

        cursor.execute('SELECT COUNT(*) FROM dbo.Offres WHERE id_catalogue = ?', (catalogue_id,))
        if cursor.fetchone()[0] > 0:
            return {'catalogue': catalogue_name, 'saved_count': 0, 'already_exists': True, 'offers': offers}

        saved_count = 0
        for offer in offers:
            cursor.execute(
                'SELECT id_offre FROM dbo.Offres WHERE id_catalogue = ? AND nom_offre = ? AND page_source = ? AND extrait_source = ?',
                (catalogue_id, offer.get('nom_offre'), offer.get('page_source'), offer.get('extrait_source')),
            )
            if cursor.fetchone():
                continue

            cursor.execute(
                'INSERT INTO dbo.Offres (id_catalogue, nom_offre, technologie, debit_mbps, prix_mensuel_ttc, engagement_mois, frais_installation_ttc, appels_inclus, conditions_offre, page_source, extrait_source, est_validee) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)',
                (
                    catalogue_id,
                    offer.get('nom_offre'),
                    offer.get('technologie') or 'Fibre',
                    offer.get('debit_mbps'),
                    offer.get('prix_mensuel_ttc'),
                    offer.get('engagement_mois'),
                    offer.get('frais_installation_ttc'),
                    offer.get('appels_inclus'),
                    offer.get('conditions_offre'),
                    offer.get('page_source'),
                    offer.get('extrait_source'),
                ),
            )
            saved_count += 1

        conn.commit()
        return {'catalogue': catalogue_name, 'saved_count': saved_count, 'already_exists': False, 'offers': offers}


def save_offers_from_preview(offers: list[dict[str, Any]], file_name: str, operator_name: str, segment: str = 'B2C', edition: str | None = None, url_source: str | None = None) -> dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        operator_id = ensure_operator(cursor, operator_name)
        catalogue_id = ensure_catalogue(cursor, operator_id, file_name, edition, segment, url_source)

        cursor.execute('SELECT COUNT(*) FROM dbo.Offres WHERE id_catalogue = ?', (catalogue_id,))
        if cursor.fetchone()[0] > 0:
            return {'catalogue': file_name, 'saved_count': 0, 'already_exists': True, 'offers': offers}

        saved_count = 0
        for offer in offers:
            if not offer.get('nom_offre'):
                continue
            cursor.execute(
                'INSERT INTO dbo.Offres (id_catalogue, nom_offre, technologie, debit_mbps, prix_mensuel_ttc, engagement_mois, frais_installation_ttc, appels_inclus, conditions_offre, page_source, extrait_source, est_validee) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)',
                (
                    catalogue_id,
                    offer.get('nom_offre'),
                    offer.get('technologie') or 'Fibre',
                    offer.get('debit_mbps'),
                    offer.get('prix_mensuel_ttc'),
                    offer.get('engagement_mois'),
                    offer.get('frais_installation_ttc'),
                    offer.get('appels_inclus'),
                    offer.get('conditions_offre'),
                    offer.get('page_source'),
                    offer.get('extrait_source'),
                ),
            )
            saved_count += 1

        conn.commit()
        return {'catalogue': file_name, 'saved_count': saved_count, 'already_exists': False, 'offers': offers}
