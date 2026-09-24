import sys
from pathlib import Path
from datetime import datetime
import json
import re
from dateutil import parser
from pydantic import ValidationError


BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from app.models import ResponseCreate


def json_consumer(json_path):
    raw_data = None
    with open(json_path, 'r', encoding='UTF-8') as f:
        raw_data = json.load(f)

    return raw_data

def data_validation(raw_data: list[dict] | dict):
    if isinstance(raw_data, dict):
            raw_data = [raw_data]
    
    all_valid_data = []
    errors = []

    for data in raw_data:
            try:
                validated_data = ResponseCreate.model_validate(data)
            except ValidationError as e:
                errors.append({'item': data, 'error': e.errors()})
                continue

            if validated_data.id not in [valid_data['origin_id'] for valid_data in all_valid_data]:                
                new_data = {
                    'origin_id': validated_data.id,
                    'question': validated_data.pergunta,
                    'platform': validated_data.plataforma,
                    'model': validated_data.modelo,
                    'response_text': validated_data.resposta_texto,
                    'date_hour': validated_data.data_hora,
                    'sentiment': validated_data.sentimento
                }
                
                all_valid_data.append(new_data)

    return all_valid_data, errors

def data_cleansing(validated_data: list[dict]):
    """Data cleansing and normalization before database persistency"""

    if isinstance(validated_data, dict):
        validated_data = [validated_data]

    plataforma_variations_mapper = {
        r"(?i)^chat[-_\s]?gpt$": "ChatGPT",
        r"(?i)^gemini$": "Gemini",     
        r"(?i)^perplexity$": "Perplexity"
    }

    all_clean_data = []
    
    for valid_data in validated_data:
        # Response text and question validation
        if not valid_data.get('response_text') or not valid_data.get('question'):
            continue

        # Platform treatment
        if valid_data.get('platform'):
            for pattern, correct_name in plataforma_variations_mapper.items():
                if re.match(pattern, valid_data['platform']):
                    valid_data['platform'] = correct_name
        else:
            continue

        # Datetime treatment
        try:
            if valid_data.get('date_hour') is not None:
                valid_data['date_hour'] = parser.parse(valid_data['date_hour'])
            else:
                valid_data['date_hour'] = None
        except (ValueError, TypeError):
            valid_data['date_hour'] = None # How datetime will not be used in analysis, I must prefer maintain the data and set datetime.now() as default

        all_clean_data.append(valid_data)

    return all_clean_data


def brand_mention_detector(ai_response: str) -> list:
    """Function that recognizes brand mentions using regex to consider writing variations"""
    brand_mentions_found = []

    if not ai_response:
        return brand_mentions_found

    # Brand writing variations
    BRAND_PATTERNS = {
        'Acme': re.compile(r'\ba\.?\s*c\.?\s*m\.?\s*e\.?\b', re.IGNORECASE),
        'Zenith': re.compile(r'\bzenith\b', re.IGNORECASE),
        'Nimbus': re.compile(r'\bnimbus\b', re.IGNORECASE)
    }
        
    for brand, pattern in BRAND_PATTERNS.items():
        if pattern.search(ai_response):
            brand_mentions_found.append(brand)

    return brand_mentions_found