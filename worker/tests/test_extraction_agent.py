from types import SimpleNamespace

from app.services.extraction_agent import MAX_TOOL_ITERATIONS, run_extraction_agent


class FakeMessages:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        # snapshot messages: a real API call serializes the payload at call
        # time, so later in-place mutation of the list must not leak back.
        self.calls.append({**kwargs, "messages": list(kwargs["messages"])})
        return self._responses.pop(0)


class FakeClient:
    def __init__(self, responses):
        self.messages = FakeMessages(responses)


def _tool_use(name, input_, id_="tool_1"):
    return SimpleNamespace(type="tool_use", name=name, input=input_, id=id_)


def test_agent_uses_tool_result_then_submits(db_session_factory) -> None:
    db = db_session_factory()
    responses = [
        SimpleNamespace(
            content=[
                _tool_use("convert_units", {"value": 1000, "from_unit": "mg", "to_unit": "g"})
            ],
            stop_reason="tool_use",
        ),
        SimpleNamespace(
            content=[
                _tool_use(
                    "submit_extraction",
                    {"fields": [{"name": "mass", "value": 1.0, "unit": "g", "confidence": 0.95}]},
                    id_="tool_2",
                )
            ],
            stop_reason="tool_use",
        ),
    ]
    client = FakeClient(responses)

    result = run_extraction_agent(db, "process_log", ["texto de la pagina"], client=client)

    assert result == {"fields": [{"name": "mass", "value": 1.0, "unit": "g", "confidence": 0.95}]}
    assert len(client.messages.calls) == 2
    # the tool result fed back to the model must carry the converted value
    second_call_messages = client.messages.calls[1]["messages"]
    tool_result_content = second_call_messages[-1]["content"][0]["content"]
    assert "1.0" in tool_result_content
    db.close()


def test_agent_reports_tool_errors_back_without_crashing(db_session_factory) -> None:
    db = db_session_factory()
    responses = [
        SimpleNamespace(
            content=[_tool_use("calculate", {"expression": "not a valid expr!"})],
            stop_reason="tool_use",
        ),
        SimpleNamespace(
            content=[
                _tool_use(
                    "submit_extraction",
                    {"fields": [{"name": "x", "value": 1, "unit": None, "confidence": 0.5}]},
                    id_="tool_2",
                )
            ],
            stop_reason="tool_use",
        ),
    ]
    client = FakeClient(responses)

    result = run_extraction_agent(db, "process_log", ["texto"], client=client)

    assert result is not None
    second_call_messages = client.messages.calls[1]["messages"]
    tool_result_content = second_call_messages[-1]["content"][0]["content"]
    assert "error" in tool_result_content
    db.close()


def test_agent_returns_none_when_iterations_exhausted(db_session_factory) -> None:
    db = db_session_factory()
    responses = [
        SimpleNamespace(
            content=[_tool_use("calculate", {"expression": "1 + 1"})], stop_reason="tool_use"
        )
        for _ in range(MAX_TOOL_ITERATIONS)
    ]
    client = FakeClient(responses)

    result = run_extraction_agent(db, "process_log", ["texto"], client=client)

    assert result is None
    assert len(client.messages.calls) == MAX_TOOL_ITERATIONS
    db.close()
