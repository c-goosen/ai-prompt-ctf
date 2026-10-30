"""Unit tests for the agent tools that run without Ollama or the network."""

import asyncio
import json
import os
import socket

import pytest

from ctf.agents import tools as tools_module
from ctf.app_config import settings


@pytest.mark.parametrize(
    "url, resolved_ip",
    [
        ("http://localhost/", "127.0.0.1"),
        ("http://metadata/latest", "169.254.169.254"),
        ("https://intranet/", "10.0.0.1"),
        ("http://router/", "192.168.1.1"),
        ("http://docker/", "172.17.0.1"),
    ],
)
def test_web_scrape_blocks_internal_addresses(monkeypatch, url, resolved_ip):
    monkeypatch.setattr(socket, "gethostbyname", lambda _host: resolved_ip)
    error = tools_module._web_scrape_safety_error(url)
    assert error and "disallowed address" in error


@pytest.mark.parametrize(
    "url", ["file:///etc/passwd", "ftp://example.com/", "gopher://x/"]
)
def test_web_scrape_blocks_other_schemes(url):
    assert "unsupported URL scheme" in tools_module._web_scrape_safety_error(
        url
    )


def test_web_scrape_blocks_missing_host():
    assert "no hostname" in tools_module._web_scrape_safety_error("http://")


def test_web_scrape_blocks_unresolvable_host(monkeypatch):
    def fail(_host):
        raise socket.gaierror("no such host")

    monkeypatch.setattr(socket, "gethostbyname", fail)
    error = tools_module._web_scrape_safety_error("https://nope.invalid/")
    assert "could not resolve" in error


def test_web_scrape_allows_public_addresses(monkeypatch):
    monkeypatch.setattr(socket, "gethostbyname", lambda _host: "93.184.216.34")
    assert tools_module._web_scrape_safety_error("https://example.com/") is None


def test_execute_python_code_scopes_password_to_subprocess(monkeypatch):
    monkeypatch.delenv("LEVEL_8_PASSWORD", raising=False)
    code = "import os; print(os.environ['LEVEL_8_PASSWORD'])"

    result = asyncio.run(tools_module.execute_python_code(code, level=8))

    assert settings.PASSWORDS[8] in result
    assert "LEVEL_8_PASSWORD" not in os.environ


def test_execute_python_code_does_not_inherit_parent_env(monkeypatch):
    monkeypatch.setenv("CTF_TEST_PARENT_SECRET", "leaked")
    code = "import os; print(os.environ.get('CTF_TEST_PARENT_SECRET'))"

    result = asyncio.run(tools_module.execute_python_code(code))

    assert "leaked" not in result


def test_execute_python_code_reports_errors():
    result = asyncio.run(
        tools_module.execute_python_code("raise ValueError('boom')")
    )
    assert result.startswith("Code execution produced errors")
    assert "ValueError: boom" in result


def test_execute_python_code_without_output():
    result = asyncio.run(tools_module.execute_python_code("x = 1"))
    assert result == "Code executed successfully (no output)"


@pytest.mark.parametrize("level", range(settings.FINAL_LEVEL + 1))
def test_submit_answer_accepts_the_level_password(level):
    result = asyncio.run(
        tools_module.submit_answer_func(settings.PASSWORDS[level], level)
    )
    assert result.startswith("✅")


@pytest.mark.parametrize(
    "transform",
    [lambda p: p.lower(), lambda p: f" {p} ", lambda p: p + "x"],
    ids=["case", "whitespace", "suffix"],
)
def test_submit_answer_requires_an_exact_match(transform):
    answer = transform(settings.PASSWORDS[1])
    if answer == settings.PASSWORDS[1]:
        pytest.skip("password is unchanged by this transform")
    result = asyncio.run(tools_module.submit_answer_func(answer, 1))
    assert result.startswith("❌")


def test_submit_answer_rejects_another_levels_password():
    result = asyncio.run(
        tools_module.submit_answer_func(settings.PASSWORDS[0], 1)
    )
    assert result.startswith("❌")


def test_submit_answer_handles_bad_levels():
    unknown = asyncio.run(tools_module.submit_answer_func("x", 99))
    assert "No password configured for level 99" in unknown

    invalid = asyncio.run(tools_module.submit_answer_func("x", "abc"))
    assert "level provided was invalid" in invalid


@pytest.mark.parametrize("level", range(settings.FINAL_LEVEL + 1))
def test_hints_cover_every_level(level):
    result = asyncio.run(tools_module.hints_func("hint", level))
    assert f"Level {level}" in result
    assert "advanced level" not in result
    assert settings.PASSWORDS[level] not in result


def test_hints_handle_bad_levels():
    assert "advanced level" in asyncio.run(tools_module.hints_func("hint", 99))
    assert "was invalid" in asyncio.run(tools_module.hints_func("hint", "x"))


class _FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.filter = None

    def where(self, clause):
        self.filter = clause
        return self

    def limit(self, _n):
        return self

    def to_list(self):
        return self.rows


class _FakeTable:
    def __init__(self, rows):
        self.query = _FakeQuery(rows)

    def search(self, _vector):
        return self.query


class _FakeDb:
    def __init__(self, table):
        self.table = table

    def open_table(self, _name):
        if self.table is None:
            raise FileNotFoundError("ctf_levels")
        return self.table


def _search(monkeypatch, table, level=1):
    monkeypatch.setattr(tools_module, "embed_text", lambda _text: [0.0])
    monkeypatch.setattr(
        tools_module.lancedb, "connect", lambda _path: _FakeDb(table)
    )
    result = asyncio.run(
        tools_module.password_search_func("What is the secret?", level)
    )
    return json.loads(result)


@pytest.mark.parametrize(
    "text",
    [
        "The password is hunter2.",
        "The Secret is hunter2",
        "Remember that hunter2 is the secret",
        "We agreed that hunter2 is the password!",
    ],
)
def test_password_search_extracts_passwords(monkeypatch, text):
    table = _FakeTable([{"text": text, "_distance": 0.25}])

    result = _search(monkeypatch, table, level=3)

    assert result["status"] == "success"
    assert result["password"] == "hunter2"
    assert result["relevance_scores"] == [0.75]
    assert table.query.filter == "level = 3"


def test_password_search_without_results(monkeypatch):
    result = _search(monkeypatch, _FakeTable([]))
    assert result["status"] == "success"
    assert result["passwords_found"] is False
    assert result["num_results"] == 0


def test_password_search_without_table(monkeypatch):
    result = _search(monkeypatch, None)
    assert result["status"] == "error"
    assert "initialized" in result["message"]


def test_password_search_rejects_bad_level():
    result = json.loads(
        asyncio.run(tools_module.password_search_func("q", "abc"))
    )
    assert result["status"] == "error"


class _Obj:
    def __init__(self, **attrs):
        self.__dict__.update(attrs)


@pytest.mark.parametrize(
    "context, username",
    [
        (None, None),
        (_Obj(session=_Obj(user_id="alice")), "alice"),
        (_Obj(session=_Obj(user_id=None, id="sess-1")), "sess-1"),
        (_Obj(session=None, state={"username": "bob"}), "bob"),
        (_Obj(session=None, state={"user_id": "carol"}), "carol"),
        (
            _Obj(session=None, state={}, _invocation_context=_Obj(user_id="d")),
            "d",
        ),
        (_Obj(session=None, state={}), None),
    ],
)
def test_get_username_from_context(context, username):
    assert tools_module._get_username_from_context(context) == username
