"""
Data Application Tests.
"""

import pytest

from kelvin_checker import App


@pytest.fixture
def app() -> App:
    """Application fixture."""

    app = App()
    app.config.kelvin.app.offset_timestamps = True

    return app


def test_init(app: App) -> None:
    """Test initialization of application."""

    assert isinstance(app, App)


def test_in_range(app: App) -> None:
    """Test application if pressure in range."""

    message = app.make_message("raw.float32", "pressure", time_of_validity=1e9, value=100.0)
    app.on_data([message])

    assert app.data.pressure is message
    assert [*app.data.history.pressure] == [message]

    outputs = app.context.get_outputs()
    assert len(outputs) == 1
    result = outputs[0]
    assert result._.type == "raw.float32"
    assert result._.name == "doubled_pressure"
    assert result._.time_of_validity == message._.time_of_validity
    assert result.value == 2.0 * message.value


def test_outside_range(app: App) -> None:
    """Test application if pressure outside range."""

    message = app.make_message("raw.float32", "pressure", time_of_validity=1e9, value=-100.0)
    app.on_data([message])

    assert app.data.pressure is message
    assert [*app.data.history.pressure] == [message]

    outputs = app.context.get_outputs()
    assert not outputs
