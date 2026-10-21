"""Common pytest wiring. All production-interface knowledge stays in invocation."""

import pytest

from tests.support.data import fixture_path, load_json
from tests.support.invocation import get_invocation


@pytest.fixture
def invoke():
    return get_invocation()


@pytest.fixture
def source_path():
    return fixture_path


@pytest.fixture
def source_json():
    return load_json


@pytest.fixture
def run(invoke, tmp_path):
    """Focus graph tests explicitly on provenance=none and a supplied base.

    Other controls remain absent unless the test supplies them. Tests of base
    omission/configuration rejection call the binding directly instead.
    """
    def convert(key="shared/core_model", filename="input.json", *, path=None, **options):
        effective_request = {"base_iri": "https://example.test/model#", "provenance": "none"}
        effective_request.update(options)
        source = path if path is not None else fixture_path(key, filename)
        return invoke.convert(source, options=effective_request, workdir=tmp_path)
    return convert
