from unittest.mock import MagicMock, patch

import pytest

from app.services.analyzers.nlp_service import NLPInferenceService


@pytest.fixture
def service():
    instance = NLPInferenceService()
    instance._pipeline = MagicMock()
    return instance


def test_predict_success(service):
    service._pipeline.predict_proba.return_value = [ [0.2, 0.8] ]
    service._extract_top_tokens = MagicMock(return_value=["verify", "account"])

    result = service.predict("Verify your account immediately")

    assert result["status"] == "success"
    assert result["phishing_probability"] == 0.8
    assert result["is_phishing"] is True
    assert result["top_indicative_tokens"] == ["verify", "account"]


def test_predict_unavailable_model(service):
    service._pipeline = None

    result = service.predict("Please verify your account")

    assert result["status"] == "unavailable"
    assert result["phishing_probability"] is None
    assert result["is_phishing"] is None


@pytest.mark.parametrize("text", ["", "   ", None, 123])
def test_predict_invalid_input(service, text):
    result = service.predict(text)

    assert result["status"] == "invalid_input"
    assert result["phishing_probability"] is None
    assert result["is_phishing"] is None


def test_predict_exception_does_not_report_safe_email(service):
    service._pipeline.predict_proba.side_effect = RuntimeError("Model failure")

    result = service.predict("Please verify your account")

    assert result["status"] == "error"
    assert result["phishing_probability"] is None
    assert result["is_phishing"] is None  