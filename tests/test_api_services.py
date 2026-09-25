import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from app.services import ResponseService, BrandService, MentionService

def _seed_responses(session):
    """População do banco de dados de teste"""

    service = ResponseService(session)
    payloads = [
        {"id": "r1", "pergunta": "Pergunta?", "plataforma": "ChatGPT", "resposta_texto": "A Acme lidera."},
        {"id": "r2", "pergunta": "Pergunta?", "plataforma": "ChatGPT", "resposta_texto": "Texto sem marca."},
        {"id": "r3", "pergunta": "Pergunta?", "plataforma": "Gemini", "resposta_texto": "A Acme também é boa."},
        {"id": "r4", "pergunta": "Pergunta?", "plataforma": "Gemini", "resposta_texto": "Texto sem marca também."},
    ]
    for payload in payloads:
        service.create_response(payload)


def test_unknown_brand_returns_404(session):
    """Teste para validar se marca não monitorada não é encontrada"""

    service = BrandService(session)
    with pytest.raises(HTTPException) as exc_info:
        service.get_share_of_voice("MarcaInexistente")

    assert exc_info.value.status_code == 404


def test_percentage_by_platform_is_correct(session):
    """Teste para verificar percentual e valores absolutos por plataforma"""

    _seed_responses(session)
    service = BrandService(session)

    result = service.get_share_of_voice("Acme")
    by_platform = result["percentual_marca_por_plataforma"]

    assert by_platform["ChatGPT"]["percentual"] == 50.0
    assert by_platform["ChatGPT"]["total_respostas"] == 2
    assert by_platform["ChatGPT"]["total_marca"] == 1

    assert by_platform["Gemini"]["percentual"] == 50.0
    assert by_platform["Gemini"]["total_respostas"] == 2
    assert by_platform["Gemini"]["total_marca"] == 1


def test_overall_totals_are_correct(session):
    """Teste para verificar os valores absolutos gerais retornados junto ao percentual"""

    _seed_responses(session)
    service = BrandService(session)

    result = service.get_share_of_voice("Acme")

    assert result["total_respostas"] == 4
    assert result["total_marca_em_respostas"] == 2
    assert result["percentual_marca_em_respostas"] == 50.0


def test_returns_ranked_list(client):
    """Teste para verificar se o ranking funciona"""

    client.post("/respostas", json={
        "id": "r001", "pergunta": "P?", "plataforma": "ChatGPT",
        "resposta_texto": "Acme, Zenith e Nimbus juntas nesta resposta.",
    })

    client.post("/respostas", json={
        "id": "r002", "pergunta": "P?", "plataforma": "Gemini",
        "resposta_texto": "Apenas Acme por aqui.",
    })

    response = client.get("/top-citacoes", params={"n": 5})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["origin_id"] == "r001"


def test_platform_with_zero_mentions_still_appears(session):
    """Teste para verificar se plataforma sem nenhuma menção da marca não pode desaparecer do resultado,
    ela deve aparecer com 0.0%."""

    service = ResponseService(session)
    service.create_response({
        "id": "r1", "pergunta": "Pergunta?", "plataforma": "Perplexity",
        "resposta_texto": "Nenhuma marca monitorada aqui.",
    })

    brand_service = BrandService(session)
    result = brand_service.get_share_of_voice("Acme")
    perplexity = result["percentual_marca_por_plataforma"]["Perplexity"]

    assert perplexity["percentual"] == 0.0
    assert perplexity["total_respostas"] == 1
    assert perplexity["total_marca"] == 0


def test_ties_in_distinct_brands_broken_by_occurrence_count(session):
    """Teste para verificar se duas respostas com o mesmo número de marcas
    distintas são desempatadas pela soma de ocorrências de cada marca no texto."""

    service = ResponseService(session)

    # Ambas citam 2 marcas distintas, mas r2 repete "Acme" três vezes
    service.create_response({
        "id": "r1", "pergunta": "Pergunta?", "plataforma": "ChatGPT",
        "resposta_texto": "Acme e Zenith competem no setor.",
    })
    service.create_response({
        "id": "r2", "pergunta": "Pergunta?", "plataforma": "Gemini",
        "resposta_texto": "Acme lidera. A Acme é boa. A Acme cresce. Zenith acompanha.",
    })

    mention_service = MentionService(session)
    top = mention_service.get_top_citations(n=5)

    assert top[0]["origin_id"] == "r2"
    assert top[0]["marcas_distintas_citadas"] == 2
    assert top[0]["total_de_ocorrencias"] == 4  # 3x Acme + 1x Zenith

    assert top[1]["origin_id"] == "r1"
    assert top[1]["total_de_ocorrencias"] == 2