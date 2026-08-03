"""Client utilities for interacting with a local Ollama instance."""

import json
import math
import os
from typing import Dict, Iterator, Optional, Sequence, Tuple, Union

from urllib import error, request
from urllib.parse import urljoin


DEFAULT_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/")
DEFAULT_MODEL = os.getenv(
    "OLLAMA_MODEL", "transactions-classifier-model:latest"
)
_GENERATE_PATH = "api/generate"


class OllamaClientError(RuntimeError):
    """Raised when the Ollama API returns an error or unexpected payload."""


def _build_generate_url(base_url: str) -> str:
    base = base_url if base_url.endswith("/") else f"{base_url}/"
    return urljoin(base, _GENERATE_PATH)


def _stream_chunks(url: str, payload: Dict[str, object], timeout: int) -> Iterator[Dict[str, object]]:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                yield json.loads(line)
    except error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="ignore")
        raise OllamaClientError(
            f"Ollama request failed with status {exc.code}: {message}"
        ) from exc
    except error.URLError as exc:
        raise OllamaClientError(f"Unable to reach Ollama server: {exc.reason}") from exc


def _extract_logprob_values(chunk: Dict[str, object]) -> Sequence[float]:
    values: list[float] = []
    logprobs = chunk.get("logprobs")
    if isinstance(logprobs, (int, float)):
        values.append(float(logprobs))
    elif isinstance(logprobs, dict):
        tokens = logprobs.get("tokens")
        if isinstance(tokens, list):
            for token_info in tokens:
                if isinstance(token_info, dict):
                    logprob = token_info.get("logprob")
                    if isinstance(logprob, (int, float)):
                        values.append(float(logprob))
    elif isinstance(logprobs, list):
        for entry in logprobs:
            if isinstance(entry, dict):
                logprob = entry.get("logprob")
                if isinstance(logprob, (int, float)):
                    values.append(float(logprob))
            elif isinstance(entry, (int, float)):
                values.append(float(entry))
    return values


def _calculate_confidence(logprob_values: Sequence[float]) -> Optional[float]:
    if not logprob_values:
        return None
    avg_logprob = sum(logprob_values) / len(logprob_values)
    return math.exp(avg_logprob)


def query_ollama(
    prompt: str,
    *,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    system_prompt: Optional[str] = None,
    options: Optional[Dict[str, object]] = None,
    timeout: int = 60,
    return_confidence: bool = False,
) -> Union[str, Tuple[str, Optional[float]]]:
    """
    Send a prompt to Ollama and return the full generated response text.

    If `return_confidence` is True and token log-probabilities are provided, also
    return a confidence score computed as exp(mean(token_logprob)).
    """

    payload: Dict[str, object] = {
        "model": model or DEFAULT_MODEL,
        "prompt": prompt,
    }

    if system_prompt:
        payload["system"] = system_prompt

    options_payload: Optional[Dict[str, object]] = None
    if options:
        options_payload = dict(options)
    if return_confidence:
        if options_payload is None:
            options_payload = {}
        options_payload.setdefault("logprobs", 1)
    if options_payload:
        payload["options"] = options_payload

    url = _build_generate_url(base_url or DEFAULT_BASE_URL)
    response_parts: list[str] = []
    logprob_values: list[float] = []

    for chunk in _stream_chunks(url, payload, timeout):
        if chunk.get("error"):
            raise OllamaClientError(str(chunk["error"]))

        piece = chunk.get("response")
        if piece:
            response_parts.append(piece)
        # print('chunk',chunk)

        logprob_values.extend(_extract_logprob_values(chunk))
        # print('logprob_values', logprob_values)

        if chunk.get("done"):
            break

    if not response_parts:
        raise OllamaClientError("Ollama returned no content for the prompt.")

    response_text = "".join(response_parts).strip()
    if return_confidence:
        confidence = _calculate_confidence(logprob_values)
        return response_text, confidence
    return response_text


_TRANSACTION_PROMPT_TEMPLATE = (
    "You are a financial transaction classifier.\n\n"
    "Choose ONLY one category:\n"
    "Income,Food,TransferFrom,Others,TransferTo,Grocery,Savings,Monthly,Investment,"
    "Transportation,Entertainment,Reload,Self-invest,MoneyExchange,Trip,Insurance,"
    "Subscription & Utility Charges,Credit Card Payment,Rental\n\n"
    "Transaction:{transaction}\n    \n"
    "Return only the category."
)


def transaction_classifier_model(
    transaction: str,
    *,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    options: Optional[Dict[str, object]] = None,
    timeout: int = 60,
    return_confidence: bool = False,
) -> Union[str, Tuple[str, Optional[float]]]:
    """Classify a transaction description using the Ollama transaction model."""

    prompt = _TRANSACTION_PROMPT_TEMPLATE.format(transaction=transaction.strip())
    return query_ollama(
        prompt,
        model=model,
        base_url=base_url,
        options=options,
        timeout=timeout,
        return_confidence=return_confidence,
    )


__all__ = ["query_ollama", "OllamaClientError", "transaction_classifier_model"]
