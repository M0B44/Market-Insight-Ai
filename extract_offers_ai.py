from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from llm_client import call_llm_json, llm_available


class ExtractedOffer(BaseModel):
    model_config = ConfigDict(extra='forbid')

    nom_offre: str | None = Field(default=None)
    technologie: str | None = Field(default=None)
    debit_mbps: int | None = Field(default=None)
    prix_mensuel_ttc: float | None = Field(default=None)
    engagement_mois: int | None = Field(default=None)
    frais_installation_ttc: float | None = Field(default=None)
    appels_inclus: str | None = Field(default=None)
    conditions_offre: str | None = Field(default=None)
    page_source: int | None = Field(default=None)
    extrait_source: str | None = Field(default=None)

    @field_validator('technologie')
    @classmethod
    def normalize_technologie(cls, value):
        if value is None:
            return value
        return value.strip() or None

    @field_validator('extrait_source')
    @classmethod
    def validate_extrait_source(cls, value):
        if value is None:
            return value
        cleaned = ' '.join(value.split())
        return cleaned[:2000] if len(cleaned) > 2000 else cleaned


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace(' ', '').replace('DH', '').replace('Dhs', '').replace('TTC', '').replace(',', '.')
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _parse_debit_mbps(value: str | None) -> int | None:
    if value is None:
        return None
    match = re.search(r'(\d+)\s*(Mb|Gb)\s*/\s*s', value, flags=re.IGNORECASE)
    if not match:
        return None
    magnitude = int(match.group(1))
    unit = match.group(2).lower()
    return magnitude * 1000 if unit == 'gb' else magnitude


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = ' '.join(value.split())
    return cleaned[:2000] if cleaned else None


def _extract_price_from_line(line: str) -> float | None:
    if 'DH' not in line.upper():
        return None
    match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:DH|DHS)\s*(?:TTC)?', line, flags=re.IGNORECASE)
    if not match:
        return None
    return _to_float(match.group(1))


def _extract_generic_fibre_from_page(page_text: str, page_number: int) -> list[dict[str, Any]]:
    if not re.search(r'Fibre|fibre|La Fibre|Fibre Optique', page_text, flags=re.IGNORECASE):
        return []
    if re.search(r'ADSL|Dar Box 4G\+|Internet 4G|4G\+', page_text, flags=re.IGNORECASE) and not re.search(r'Fibre|Fibre Optique|La Fibre', page_text, flags=re.IGNORECASE):
        return []

    page_lines = [line.strip() for line in page_text.splitlines() if line.strip()]
    speed_positions: list[tuple[int, int]] = []
    for idx, line in enumerate(page_lines):
        if re.search(r'ADSL|Dar Box 4G\+|Internet 4G|4G\+', line, flags=re.IGNORECASE):
            continue
        match = re.search(r'(?<![A-Za-z])(\d{1,4})\s*(?:M[ée]?ga|Mb|Mbps)', line, flags=re.IGNORECASE)
        if match:
            speed_positions.append((idx, int(match.group(1))))

    if not speed_positions:
        return []

    price_positions: list[tuple[int, float]] = []
    for idx, line in enumerate(page_lines):
        if re.search(r'Frais|Engagement|Durée|Routeur|Téléphone|Box|SIM|Mise à disposition|Mise en service|FMS|Appels|Min|M[ée]?ga|Mb|Mbps', line, flags=re.IGNORECASE):
            continue
        match = re.search(r'(\d{2,4})\s*(?:DH|DHS|Dhs|MAD)\s*(?:TTC)?', line, flags=re.IGNORECASE)
        if match:
            price_positions.append((idx, float(match.group(1))))

    results: list[dict[str, Any]] = []
    for idx, debit in speed_positions:
        candidate_prices = []
        for price_idx, price in price_positions:
            if abs(price_idx - idx) <= 30:
                candidate_prices.append((abs(price_idx - idx), price))
        price = min(candidate_prices, key=lambda item: item[0])[1] if candidate_prices else None
        if price is None:
            continue

        snippet_lines = []
        for j in range(max(0, idx - 2), min(len(page_lines), idx + 10)):
            current = page_lines[j]
            if re.search(r'^(?:Offre|Nos offres|La Fibre|Tarifs|Forfait|Frais|Durée|Routeur|Box|SIM|Téléphone|Appels|Internet|Voix)', current, flags=re.IGNORECASE):
                if snippet_lines:
                    break
                continue
            snippet_lines.append(current)
        snippet = ' '.join(snippet_lines)
        snippet = re.sub(r'\s+', ' ', snippet).strip()
        if not snippet:
            snippet = page_lines[idx]

        results.append({
            'nom_offre': f'Fibre {debit} Mbps',
            'technologie': 'Fibre',
            'debit_mbps': debit,
            'prix_mensuel_ttc': price,
            'engagement_mois': None,
            'frais_installation_ttc': None,
            'appels_inclus': _clean_text(snippet)[:500],
            'conditions_offre': _clean_text(snippet)[:500],
            'page_source': page_number,
            'extrait_source': _clean_text(snippet)[:500],
        })

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int]] = set()
    for offer in results:
        key = (offer['nom_offre'], offer['page_source'], offer['debit_mbps'])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(offer)
    return deduped


def _extract_offer_from_page(page_text: str, page_number: int) -> list[dict[str, Any]]:
    if re.search(r'Offres?\s+ADSL|MT\s*Box\s*ADSL|ADSL\s*Provisoire|\bADSL\b', page_text, flags=re.IGNORECASE):
        return []

    page_lines = [line.strip() for line in page_text.splitlines() if line.strip()]
    lines = [line for line in page_lines if line not in {'+', '*'}]

    price_candidates = []
    for line in lines:
        if re.search(r"Frais\s*(?:d['’]|de\s*)?installation", line, flags=re.IGNORECASE):
            continue
        price = _extract_price_from_line(line)
        if price is not None:
            price_candidates.append(price)

    speed_indexes: list[tuple[int, int]] = []
    for idx, line in enumerate(lines):
        match = re.search(r'(?:Accès\s+)?Fibre\s+Optique\s*(\d+)\s*(Mb|Gb)\s*/\s*s|\b(\d+)\s*(Mb|Gb)\s*/\s*s\b', line, flags=re.IGNORECASE)
        if not match:
            continue
        debit = _parse_debit_mbps(f"{match.group(1) or match.group(3)} {match.group(2) or match.group(4)}/s")
        if debit is not None:
            speed_indexes.append((idx, debit))

    if not speed_indexes:
        generic = _extract_generic_fibre_from_page(page_text, page_number)
        if generic:
            return generic
        return []

    engagement_match = re.search(r'Engagement\s*:?\s*(\d+)\s*mois', page_text, flags=re.IGNORECASE)
    installation_match = re.search(r"Frais\s*(?:d['’]|de\s*)?installation\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:DH|DHS)\s*(?:TTC)?", page_text, flags=re.IGNORECASE)

    last_speed_index = max(index for index, _ in speed_indexes)
    service_block_lines: list[str] = []
    for forward_idx in range(last_speed_index + 1, min(len(lines), last_speed_index + 80)):
        current = lines[forward_idx]
        if re.search(r'^(?:\(\*\)|NB\.|Offres?\b|Internet\s+Très|Haut\s+Débit|\d+\.\s*Offre|MT\s*Box|Fibre\s+Optique\s+de\s+Maroc\s+Telecom)', current, flags=re.IGNORECASE):
            if service_block_lines:
                break
            continue
        if re.search(r'Accès\s+Fibre\s+Optique|Accès\s+Premium\s+MT\s+TV', current, flags=re.IGNORECASE):
            if service_block_lines:
                break
            continue
        if re.search(r'\b\d+\s*(Mb|Gb)\s*/\s*s\b', current, flags=re.IGNORECASE):
            break
        if re.search(r'\b(?:DH|DHS)\b', current, flags=re.IGNORECASE):
            continue
        if current in {'+', '*'}:
            continue
        service_block_lines.append(current)

    service_text = ' '.join(service_block_lines)
    service_text = re.sub(r'\s+', ' ', service_text).strip()
    service_text = service_text.strip(' +')
    if not service_text:
        service_text = 'Fibre Optique'

    results: list[dict[str, Any]] = []
    for idx, (_, debit) in enumerate(speed_indexes):
        price = price_candidates[idx] if idx < len(price_candidates) else None

        offer = {
            'nom_offre': f'Fibre {debit} Mbps',
            'technologie': 'Fibre',
            'debit_mbps': debit,
            'prix_mensuel_ttc': price,
            'engagement_mois': int(engagement_match.group(1)) if engagement_match else None,
            'frais_installation_ttc': _to_float(installation_match.group(1)) if installation_match else None,
            'appels_inclus': _clean_text(service_text)[:500],
            'conditions_offre': _clean_text(service_text)[:500],
            'page_source': page_number,
            'extrait_source': _clean_text(service_text)[:500],
        }
        results.append(offer)

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int]] = set()
    for offer in results:
        key = (offer['nom_offre'], offer['page_source'], offer['debit_mbps'])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(offer)
    return deduped


def _call_llm_for_page(page_text: str, page_number: int) -> list[dict[str, Any]]:
    if not llm_available():
        return _extract_offer_from_page(page_text, page_number)

    prompt = f"""
Tu es un assistant d’extraction de catalogues telecom. Extrait uniquement les offres Fibre B2C du document.
Retourne un tableau JSON valide, sans texte supplémentaire.
Chaque objet doit contenir uniquement :
nom_offre, technologie, debit_mbps, prix_mensuel_ttc, engagement_mois, frais_installation_ttc, appels_inclus, conditions_offre, page_source, extrait_source.
Règles :
- null si inconnue, jamais inventer.
- Ne mélange pas débit Mbps et volume Go.
- Conserve l’extrait exact de la page qui justifie l’offre.
- Si une information manque, mets null.
- La clé extrait_source doit apparaître exactement dans le texte de la page.

Page {page_number} :
{page_text[:8000]}
"""
    payload = call_llm_json(prompt)
    if not isinstance(payload, list):
        return _extract_offer_from_page(page_text, page_number)

    extracted: list[dict[str, Any]] = []
    for item in payload:
        try:
            validated = ExtractedOffer.model_validate({
                **item,
                'page_source': int(item.get('page_source') or page_number),
                'technologie': str(item.get('technologie') or 'Fibre'),
                'extrait_source': item.get('extrait_source') or page_text[:2000],
            })
        except Exception:
            continue

        if validated.extrait_source:
            cleared_page = ' '.join(page_text.split())
            cleared_excerpt = ' '.join(validated.extrait_source.split())
            if cleared_excerpt not in cleared_page:
                continue
        extracted.append(validated.model_dump())

    return extracted or _extract_offer_from_page(page_text, page_number)


def extract_offers_from_pages(pages_by_number: dict[int, str], operator_name: str | None = None) -> list[dict[str, Any]]:
    all_offers: list[dict[str, Any]] = []
    for page_number, page_text in sorted(pages_by_number.items()):
        if re.search(r'Offres?\s+ADSL|MT\s*Box\s*ADSL|ADSL\s*Provisoire|\bADSL\b', page_text, flags=re.IGNORECASE):
            continue

        candidates = _call_llm_for_page(page_text, page_number)
        for item in candidates:
            if item.get('technologie') and 'fibre' not in str(item['technologie']).lower():
                continue
            if item.get('extrait_source'):
                cleared_page = ' '.join(page_text.split())
                cleared_excerpt = ' '.join(str(item['extrait_source']).split())
                if cleared_excerpt not in cleared_page:
                    continue
            offer = dict(item)
            if operator_name and not offer.get('nom_offre'):
                offer['nom_offre'] = f'{operator_name} Fibre {offer.get("debit_mbps") or "?"} Mbps'
            if offer.get('conditions_offre'):
                offer['conditions_offre'] = offer['conditions_offre'][:2000]
            all_offers.append(offer)

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str | None, int | None, int | None]] = set()
    for item in all_offers:
        key = (item.get('nom_offre'), item.get('page_source'), item.get('debit_mbps'))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped
