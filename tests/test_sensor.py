"""Tests for the sensor platform."""

from homeassistant.helpers import entity_registry as er

from .conftest import MOCK_USER_ID


async def test_tracked_application_sensors_are_distinct(hass, setup_integration):
    """Each tracked application gets its own sensor with its own usage."""
    registry = er.async_get(hass)

    entity_id_app1 = registry.async_get_entity_id(
        "sensor", "family_safety", f"{MOCK_USER_ID}_app1")
    entity_id_app2 = registry.async_get_entity_id(
        "sensor", "family_safety", f"{MOCK_USER_ID}_app2")
    assert entity_id_app1 is not None
    assert entity_id_app2 is not None

    state_app1 = hass.states.get(entity_id_app1)
    state_app2 = hass.states.get(entity_id_app2)

    # regression check: the loop variable used to be captured late, making
    # every tracked-application sensor report the last application
    assert state_app1.state == "10"
    assert state_app2.state == "20"
    assert "Minecraft" in state_app1.name
    assert "Roblox" in state_app2.name
    assert state_app1.attributes["unit_of_measurement"] == "min"


async def test_screentime_sensors(hass, setup_integration):
    """Screen time sensors report minutes with a valid unit."""
    registry = er.async_get(hass)

    used_id = registry.async_get_entity_id(
        "sensor", "family_safety", f"{MOCK_USER_ID}_screentime")
    used = hass.states.get(used_id)
    assert used.state == "30.0"  # 1_800_000 ms
    assert used.attributes["unit_of_measurement"] == "min"

    limit_id = registry.async_get_entity_id(
        "sensor", "family_safety", f"{MOCK_USER_ID}_screentime_limit")
    limit = hass.states.get(limit_id)
    assert limit.state == "60.0"  # 3_600_000 ms
    assert limit.attributes["unit_of_measurement"] == "min"


async def test_account_balance_sensor(hass, setup_integration):
    """The balance sensor reports the account balance and currency."""
    registry = er.async_get(hass)

    balance_id = registry.async_get_entity_id(
        "sensor", "family_safety", f"{MOCK_USER_ID}_account_balance")
    balance = hass.states.get(balance_id)
    assert balance.state == "5.0"
    assert balance.attributes["unit_of_measurement"] == "USD"
