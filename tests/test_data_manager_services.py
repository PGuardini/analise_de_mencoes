import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from data_manager.services import data_validation, data_cleansing, brand_mention_detector

def test_missing_required_field_is_collected_as_error():
    """Teste para validar se surge erro quando falta campos obrigatórios"""

    data = {"id": "r001", "plataforma": "ChatGPT", "resposta_texto": "Texto"}
    # falta o campo obrigatório "pergunta" em ResponseCreate

    valid_data, errors = data_validation(data)

    assert valid_data == []
    assert len(errors) == 1
    assert errors[0]["item"] == data

def test_duplicate_origin_id_is_deduplicated():
    """Teste para verificar se dados duplicados não são salvos"""

    item = {
        "id": "r003",
        "pergunta": "O que é share of voice?",
        "plataforma": "Gemini",
        "modelo": "gemini-2.5-pro",
        "resposta_texto": "Texto duplicado.",
        "data_hora": "2026-01-16",
        "sentimento": "neutro",
    }
    valid_data, errors = data_validation([item, item])

    assert len(valid_data) == 1
    assert errors == []

def test_mixed_valid_and_invalid_data():
    """Teste para verificar validação de dados com dados válidos e inválidos"""

    valid_data = {
        "id": "r001",
        "pergunta": "Pergunta?",
        "plataforma": "ChatGPT",
        "resposta_texto": "Resposta.",
    }

    invalid_data = {"id": "r002", "plataforma": "Gemini"}  # sem pergunta/resposta

    valid_data, errors = data_validation([valid_data, invalid_data])

    assert len(valid_data) == 1
    assert len(errors) == 1

def test_empty_response_text_is_discarded():
    """Teste para verificar se um registro sem resposta é descartado"""

    data = [{"origin_id": "r005", "question": "pergunta?", "platform": "ChatGPT", "response_text": ""}]

    assert data_cleansing(data) == []

def test_occurrence_count_when_brand_repeats():
    """Teste para verificar se a contagem de marcas está correta"""

    text = "A Acme é ótima. A Acme também tem bom suporte. Acme lidera o mercado."
    result = brand_mention_detector(text)
    assert result["Acme"] == 3

def test_unmonitored_brand_is_never_detected():
    """Teste para verificar limite do algoritmo de detecção de marca"""

    text = "A Umbrella Corp e a Initech dominam parte do mercado de tecnologia."
    assert brand_mention_detector(text) == {}