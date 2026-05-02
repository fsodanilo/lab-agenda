import json
import re
from datetime import datetime

import httpx
from pydantic import BaseModel

from app.infrastructure.config.settings import Settings
from app.infrastructure.logging.logger import get_logger

_CLASSIFIER_SYSTEM_PROMPT = """
Você é um classificador de intenções para um assistente de agendamento de barbearia.
Classifique a mensagem do usuário em exatamente uma das seguintes intenções:

- confirm      → o usuário quer confirmar um agendamento existente
- cancel       → o usuário quer cancelar um agendamento
- reschedule   → o usuário quer remarcar (mudar data/hora) de um agendamento
- schedule     → o usuário quer criar um NOVO agendamento e mencionou um horário
- availability → o usuário quer ver horários disponíveis para um dia (sem solicitar criação)
- question     → dúvida genérica, saudação ou qualquer outra mensagem

Regras de extração de requested_time_iso:
- Para "schedule": preencha SOMENTE se o usuário informar um horário explícito ("às 14h", "14:00").
  Se mencionar só a data sem horário, deixe null.
- Para "availability": preencha com a data consultada usando meia-noite como hora
  (ex: "2026-04-22T00:00:00"). Se o usuário disser "nesse dia", "o mesmo dia", "esse dia" etc.,
  extraia a data do histórico da conversa.
- Para outros intents: deixe null.
- Quando o usuário mencionar apenas um horário sem data (ex: "às 14"), use a data mais recente
  discutida no histórico. Se não houver histórico, use a data de hoje.

Regras para calcular datas a partir de nomes de dias da semana ("segunda", "terça", "sábado" etc.):
- Use o dia atual informado no contexto como referência.
- Se o dia mencionado for DIFERENTE do dia atual, calcule a PRÓXIMA ocorrência futura desse dia.
  Exemplo: hoje é segunda (20/04), "sábado" → próximo sábado = 25/04.
- Se o dia mencionado for IGUAL ao dia atual, use a data de hoje.
- NUNCA some apenas 2 ou 3 dias para chegar a um dia da semana; conte quantos dias faltam
  corretamente até a próxima ocorrência.

Use a data e hora atual informada no contexto (Horário de Brasília).
Retorne APENAS o rótulo da intenção, a pontuação de confiança e o horário solicitado.
""".strip()

_RESPONSE_SYSTEM_PROMPT = """
Você é um assistente de agendamento simpático e profissional da RChaves Barbearia.
Seu papel é gerar uma resposta clara e objetiva para o cliente com base nas
informações fornecidas. Não invente agendamentos, horários ou disponibilidades.
Use apenas os dados fornecidos. Responda sempre em português brasileiro.

Capacidades que você possui e pode informar ao cliente quando pertinente:
- 📅 Criar um novo agendamento (basta informar o dia e o horário desejado)
- ✅ Confirmar um agendamento existente
- ❌ Cancelar um agendamento
- 🔄 Remarcar para outro dia ou horário
- ❓ Responder dúvidas sobre a barbearia
""".strip()

_HUMAN_TEMPLATE = """
Mensagem do cliente: {user_message}
Intenção detectada: {intent}

Resultado do agendamento: {booking_result}

Agendamentos existentes (próximas 24h):
{events}

Horários disponíveis:
{slots}

Instruções por intenção e resultado:
- Se a mensagem for uma saudação ("oi", "olá", "bom dia", "boa tarde", "boa noite" etc.):
  responda a saudação cordialmente usando a mesma saudação do cliente, apresente-se brevemente
  como assistente da RChaves Barbearia e liste de forma amigável o que você pode fazer,
  convidando o cliente a escolher uma opção.
- confirmed      → o agendamento JÁ FOI CRIADO COM SUCESSO no sistema. OBRIGATORIAMENTE confirme
  ao cliente informando data e hora exibidas em "Agendamentos existentes". NUNCA diga que o
  horário não está disponível quando booking_result=confirmed.
- unavailable    → informe que o horário solicitado não está disponível e mostre os horários livres
- no_time        → peça ao cliente para informar o horário desejado; se houver horários disponíveis listados abaixo, mostre-os como sugestão
- outside_hours  → informe que o horário solicitado está fora do horário de funcionamento da barbearia.
  Informe os horários permitidos: segunda a sexta das 8h às 19h e sábado das 8h às 14h.
  Domingo não há atendimento. Convide o cliente a escolher um horário dentro desse intervalo.
- error          → informe que houve um problema técnico e peça para tentar novamente
- N/A com intent=availability → liste os horários disponíveis encontrados em "Horários disponíveis".
  Se a lista estiver vazia, informe que a agenda está cheia para aquele dia.
- N/A         → ignore o resultado e responda com base nos outros dados

Gere uma resposta útil para o cliente.
""".strip()

_JSON_BLOCK_PATTERN = re.compile(r"\{.*\}", re.DOTALL)
_GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class IntentClassification(BaseModel):
    intent: str
    confidence: float
    requested_time_iso: str | None = None


class GeminiLLMService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._logger = get_logger(__name__)

    async def classify_intent(
        self,
        user_message: str,
        history: str,
        current_datetime: datetime,
    ) -> IntentClassification:
        prompt = (
            f"Data e hora atual (Brasilia): {current_datetime.isoformat()}\n"
            f"Historico recente:\n{history or 'sem historico'}\n\n"
            f"Mensagem do usuario:\n{user_message}\n\n"
            'Responda em JSON puro com as chaves "intent", "confidence" e "requested_time_iso".'
        )
        raw_response = await self._generate_content(
            system_prompt=_CLASSIFIER_SYSTEM_PROMPT,
            user_prompt=prompt,
            response_mime_type="application/json",
            temperature=0.1,
        )
        payload = self._extract_json(raw_response)
        self._logger.info("gemini_intent_classified", extra={"intent": payload.get("intent")})
        return IntentClassification.model_validate(payload)

    async def generate_reply(
        self,
        user_message: str,
        intent: str,
        booking_result: str,
        events: str,
        slots: str,
    ) -> str:
        prompt = _HUMAN_TEMPLATE.format(
            user_message=user_message,
            intent=intent,
            booking_result=booking_result,
            events=events,
            slots=slots,
        )
        return await self._generate_content(
            system_prompt=_RESPONSE_SYSTEM_PROMPT,
            user_prompt=prompt,
            response_mime_type="text/plain",
            temperature=0.4,
        )

    async def _generate_content(
        self,
        system_prompt: str,
        user_prompt: str,
        response_mime_type: str,
        temperature: float,
    ) -> str:
        if not self._settings.gemini_api_key:
            raise ValueError("APP_GEMINI_API_KEY is not configured")
        if not self._settings.gemini_model:
            raise ValueError("APP_GEMINI_MODEL is not configured")

        url = (
            f"{_GEMINI_API_BASE_URL}/models/{self._settings.gemini_model}:generateContent"
            f"?key={self._settings.gemini_api_key}"
        )
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": response_mime_type,
            },
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
        data = response.json()
        return self._extract_text(data)

    def _extract_text(self, payload: dict[str, object]) -> str:
        candidates = payload.get("candidates", [])
        if not isinstance(candidates, list) or not candidates:
            raise ValueError("Gemini response did not include candidates")

        first_candidate = candidates[0]
        if not isinstance(first_candidate, dict):
            raise ValueError("Gemini candidate payload is invalid")

        content = first_candidate.get("content", {})
        if not isinstance(content, dict):
            raise ValueError("Gemini content payload is invalid")

        parts = content.get("parts", [])
        if not isinstance(parts, list) or not parts:
            raise ValueError("Gemini response did not include content parts")

        texts: list[str] = []
        for part in parts:
            if isinstance(part, dict):
                text = part.get("text")
                if isinstance(text, str):
                    texts.append(text)

        if not texts:
            raise ValueError("Gemini response did not include text parts")
        return "\n".join(texts).strip()

    def _extract_json(self, content: str) -> dict[str, object]:
        match = _JSON_BLOCK_PATTERN.search(content)
        if match is None:
            raise ValueError("Gemini did not return valid JSON content")
        return json.loads(match.group(0))
