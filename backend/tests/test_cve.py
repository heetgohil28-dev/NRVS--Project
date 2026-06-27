import pytest
from unittest.mock import patch, AsyncMock
from app.services.cve_service import enrich_cve, _parse_cvss, _extract_cve_ids_from_port
from app.services.mitre_service import map_cve_to_mitre
from app.services.scoring_service import calculate_host_risk_score, get_severity_from_cvss, assign_security_grade
from app.database.models import SeverityLevel


class TestCvssParser:
    def test_parse_cvss_v31(self):
        cve_item = {
            "metrics": {
                "cvssMetricV31": [{
                    "cvssData": {
                        "baseScore": 9.8,
                        "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
                    }
                }]
            }
        }
        v3, v2, vector = _parse_cvss(cve_item)
        assert v3 == 9.8
        assert v2 is None
        assert "CVSS:3.1" in vector

    def test_parse_cvss_v2_fallback(self):
        cve_item = {
            "metrics": {
                "cvssMetricV2": [{
                    "cvssData": {
                        "baseScore": 5.0,
                        "vectorString": "AV:N/AC:L/Au:N/C:N/I:N/A:P"
                    }
                }]
            }
        }
        v3, v2, vector = _parse_cvss(cve_item)
        assert v3 is None
        assert v2 == 5.0

    def test_parse_cvss_empty(self):
        v3, v2, vector = _parse_cvss({})
        assert v3 is None
        assert v2 is None
        assert vector is None


class TestSeverityMapping:
    def test_critical(self):
        assert get_severity_from_cvss(9.5) == SeverityLevel.CRITICAL

    def test_high(self):
        assert get_severity_from_cvss(7.5) == SeverityLevel.HIGH

    def test_medium(self):
        assert get_severity_from_cvss(5.0) == SeverityLevel.MEDIUM

    def test_low(self):
        assert get_severity_from_cvss(2.0) == SeverityLevel.LOW

    def test_none(self):
        assert get_severity_from_cvss(0.0) == SeverityLevel.NONE


class TestScoring:
    def test_no_vulns(self):
        assert calculate_host_risk_score([]) == 0.0

    def test_grade_a_plus(self):
        assert assign_security_grade(0.0) == "A+"
        assert assign_security_grade(9.9) == "A+"

    def test_grade_f(self):
        assert assign_security_grade(70.0) == "F"
        assert assign_security_grade(100.0) == "F"

    def test_grade_b(self):
        assert assign_security_grade(25.0) == "B"


class TestMitreMapping:
    def test_rce_mapping(self):
        result = map_cve_to_mitre("This vulnerability allows remote code execution", SeverityLevel.CRITICAL)
        assert "Execution" in result["tactics"]
        assert any(t["technique_id"] == "T1203" for t in result["techniques"])

    def test_dos_mapping(self):
        result = map_cve_to_mitre("denial of service vulnerability", SeverityLevel.MEDIUM)
        assert "Impact" in result["tactics"]
        assert any(t["technique_id"] == "T1499" for t in result["techniques"])

    def test_severity_fallback(self):
        result = map_cve_to_mitre("generic vulnerability with no keywords", SeverityLevel.CRITICAL)
        assert len(result["tactics"]) > 0
        assert len(result["techniques"]) > 0

    def test_empty_description(self):
        result = map_cve_to_mitre(None, SeverityLevel.HIGH)
        assert len(result["tactics"]) > 0

    def test_no_duplicates(self):
        result = map_cve_to_mitre("remote code execution rce buffer overflow", SeverityLevel.CRITICAL)
        ids = [t["technique_id"] for t in result["techniques"]]
        assert len(ids) == len(set(ids))


class TestCveExtraction:
    def test_extract_cve_from_script_output(self):
        mock_port = type("Port", (), {
            "script_output": {
                "vuln": "CVE-2021-41773 path traversal\nCVE-2021-42013 RCE"
            }
        })()
        cve_ids = _extract_cve_ids_from_port(mock_port)
        assert "CVE-2021-41773" in cve_ids
        assert "CVE-2021-42013" in cve_ids

    def test_no_cves_in_output(self):
        mock_port = type("Port", (), {
            "script_output": {"http-title": "Apache Server"}
        })()
        cve_ids = _extract_cve_ids_from_port(mock_port)
        assert cve_ids == []

    def test_empty_script_output(self):
        mock_port = type("Port", (), {"script_output": None})()
        cve_ids = _extract_cve_ids_from_port(mock_port)
        assert cve_ids == []

    @pytest.mark.asyncio
    @patch("app.services.cve_service._fetch_cve")
    async def test_enrich_cve_not_found(self, mock_fetch):
        mock_fetch.return_value = None
        result = await enrich_cve("CVE-9999-9999")
        assert result is None

    @pytest.mark.asyncio
    @patch("app.services.cve_service._fetch_cve")
    async def test_enrich_cve_success(self, mock_fetch):
        mock_fetch.return_value = {
            "metrics": {
                "cvssMetricV31": [{
                    "cvssData": {"baseScore": 9.8, "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"}
                }]
            },
            "descriptions": [{"lang": "en", "value": "Remote code execution vulnerability"}],
            "published": "2021-10-05T00:00:00Z",
            "references": [{"url": "https://nvd.nist.gov/vuln/detail/CVE-2021-41773"}],
            "configurations": []
        }
        result = await enrich_cve("CVE-2021-41773")
        assert result is not None
        assert result["cve_id"] == "CVE-2021-41773"
        assert result["cvss_v3_score"] == 9.8
        assert result["severity"] == SeverityLevel.CRITICAL
