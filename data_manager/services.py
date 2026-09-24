from datetime import datetime
import json
import re
from dateutil import parser

JSON_PATH = 'respostas-exemplo.json'

def json_consumer(json_path):
    raw_data = None
    with open(json_path, 'r', encoding='UTF-8') as f:
        raw_data = json.load(f)

    return raw_data



def data_cleansing(raw_data: list[dict] | dict):
    """Data ingestion first step before database persistency"""

    plataforma_variations_mapper = {
        r"(?i)^chat[-_\s]?gpt$": "ChatGPT",
        r"(?i)^gemini$": "Gemini",     
        r"(?i)^perplexity$": "Perplexity"
    }

    # List treatment
    if isinstance(raw_data, list):
        clean_data = []
        for data in raw_data:
            if data['id'] not in [d['id'] for d in clean_data]: # Check if exists double-assigned id

                if data['resposta_texto']: # Check if resposta exists

                # Platform treatment                    
                    for pattern, correct_name in plataforma_variations_mapper.items():
                        if re.match(pattern, data['plataforma']):
                            data['plataforma'] = correct_name

                # Datetime treatment
                    try:
                        data['data_hora'] = parser.parse(data['data_hora'])
                        clean_data.append(data)
                    except (ValueError, TypeError):
                        # How datetime will not be used in analysis, I must prefer maintain the data and set datetime.now() as default
                        data['data_hora'] = datetime.now()
                        clean_data.append(data)

        return clean_data

    # Single Dict treatment
    elif isinstance(raw_data, dict):
        clean_data = None
        if raw_data['resposta_texto']: # Check if resposta exists

            # Platform treatment
            for pattern, correct_name in plataforma_variations_mapper.items():
                if re.match(pattern, raw_data['plataforma']):
                    raw_data['plataforma'] = correct_name

            # Datetime treatment
            try:
                raw_data['data_hora'] = parser.parse(raw_data['data_hora'])
                clean_data = raw_data
            except (ValueError, TypeError):
                # How datetime will not be used in analysis, I must prefer maintain the data and set datetime.now() as default
                raw_data['data_hora'] = datetime.now()
                clean_data = raw_data

            return clean_data

    else:
        raise TypeError('São suportados apenas listas de dicionários e dicionários. Favor informar um tipo válido.')


def brand_mention_detector(ai_response: str):
    """Function that recognizes brand mentions using regex to consider writing variations"""

    if not ai_response:
        return [] 

    # Brand writing variations
    BRAND_PATTERNS = {
        'Acme': re.compile(r'\ba\.?\s*c\.?\s*m\.?\s*e\.?\b', re.IGNORECASE),
        'Zenith': re.compile(r'\bzenith\b', re.IGNORECASE),
        'Nimbus': re.compile(r'\bnimbus\b', re.IGNORECASE)
    }

    brand_mentions_found = []
        
    for brand, pattern in BRAND_PATTERNS.items():
        if pattern.search(ai_response):
            brand_mentions_found.append(brand)

    return brand_mentions_found