"""CLI regression tests, without network access."""

import asyncio
import pytest
from cleanslate import cli
from cleanslate.core.models import ServiceEntry, ServiceCategory


@pytest.mark.parametrize('found', [False, True])
def test_cli_scan_prints_unverified_with_cause(monkeypatch, capsys, found):
    async def scan(email):
        results = [ServiceEntry(name='GitHub', domain='github.com', category=ServiceCategory.ACCOUNT, found_via='osint')] if found else []
        return results, [{'domain': 'discord.com', 'cause': 'RuntimeError', 'hint': 'Captcha possibile'}, {'domain': 'pinterest.com', 'cause': 'HTTP 403'}]

    monkeypatch.setattr(cli, 'run_osint_scan', scan)
    asyncio.run(cli.cmd_scan('nessuno@example.com'))
    output = capsys.readouterr().out
    assert 'discord.com (RuntimeError), pinterest.com (HTTP 403)' in output
    assert 'Captcha possibile' not in output
    if found:
        assert 'GitHub (github.com)' in output
    else:
        assert 'Nessun account pubblico' in output
