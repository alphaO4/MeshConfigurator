from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


# ---------- Leaf module models ----------

class MQTTConfig(BaseModel):
    model_config = ConfigDict(extra='ignore') #, populate_by_name=True, alias_generator=to_camel
    address: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    encryption_enabled: Optional[bool] = None
    root: Optional[str] = None
    enabled: Optional[bool] = None
    json_enabled: Optional[bool] = None
    tls_enabled: Optional[bool] = None
    proxy_to_client_enabled: Optional[bool] = None
    map_reporting_enabled: Optional[bool] = None


class SerialConfig(BaseModel):
    model_config = ConfigDict(extra='ignore') #, populate_by_name=True, alias_generator=to_camel
    enabled: Optional[bool] = None
    echo: Optional[bool] = None
    rxd: Optional[int] = None
    txd: Optional[int] = None
    baud: Optional[str] = None          # e.g. "BAUD_DEFAULT"
    timeout: Optional[int] = None
    mode: Optional[str] = None          # e.g. "DEFAULT"
    override_console_serial_port: Optional[bool] = None


class ExternalNotificationConfig(BaseModel):
    model_config = ConfigDict(extra='ignore') #, populate_by_name=True, alias_generator=to_camel
    enabled: Optional[bool] = None
    output_ms: Optional[int] = None
    output: Optional[int] = None
    output_vibra: Optional[int] = None
    output_buzzer: Optional[int] = None
    active: Optional[bool] = None
    alert_message: Optional[bool] = None
    alert_message_vibra: Optional[bool] = None
    alert_message_buzzer: Optional[bool] = None
    alert_bell: Optional[bool] = None
    alert_bell_vibra: Optional[bool] = None
    alert_bell_buzzer: Optional[bool] = None
    use_pwm: Optional[bool] = None
    nag_timeout: Optional[int] = None
    use_i2s_as_buzzer: Optional[bool] = None


class StoreForwardConfig(BaseModel):
    model_config = ConfigDict(extra='ignore') #, populate_by_name=True, alias_generator=to_camel
    enabled: Optional[bool] = None
    heartbeat: Optional[bool] = None
    records: Optional[int] = None
    history_return_max: Optional[int] = None
    history_return_window: Optional[int] = None
    is_server: Optional[bool] = None


class RangeTestConfig(BaseModel):
    model_config = ConfigDict(extra='ignore') #, populate_by_name=True, alias_generator=to_camel
    enabled: Optional[bool] = None
    sender: Optional[int] = None
    save: Optional[bool] = None


class TelemetryConfig(BaseModel):
    model_config = ConfigDict(extra='ignore') #, populate_by_name=True, alias_generator=to_camel
    device_update_interval: Optional[int] = None
    environment_update_interval: Optional[int] = None
    environment_measurement_enabled: Optional[bool] = None
    environment_screen_enabled: Optional[bool] = None
    environment_display_fahrenheit: Optional[bool] = None
    air_quality_enabled: Optional[bool] = None
    air_quality_interval: Optional[int] = None
    power_measurement_enabled: Optional[bool] = None
    power_update_interval: Optional[int] = None
    power_screen_enabled: Optional[bool] = None
    health_measurement_enabled: Optional[bool] = None
    health_update_interval: Optional[int] = None
    health_screen_enabled: Optional[bool] = None


class CannedMessageConfig(BaseModel):
    model_config = ConfigDict(extra='ignore') #, populate_by_name=True, alias_generator=to_camel
    rotary1_enabled: Optional[bool] = None
    inputbroker_pin_a: Optional[int] = None
    inputbroker_pin_b: Optional[int] = None
    inputbroker_pin_press: Optional[int] = None
    inputbroker_event_cw: Optional[str] = None     # e.g. "NONE"
    inputbroker_event_ccw: Optional[str] = None    # e.g. "NONE"
    inputbroker_event_press: Optional[str] = None  # e.g. "NONE"
    updown1_enabled: Optional[bool] = None
    enabled: Optional[bool] = None
    allow_input_source: Optional[str] = None
    send_bell: Optional[bool] = None


class AudioConfig(BaseModel):
    model_config = ConfigDict(extra='ignore') #, populate_by_name=True, alias_generator=to_camel
    codec2_enabled: Optional[bool] = None
    ptt_pin: Optional[int] = None
    bitrate: Optional[str] = None   # e.g. "CODEC2_DEFAULT"
    i2s_ws: Optional[int] = None
    i2s_sd: Optional[int] = None
    i2s_din: Optional[int] = None
    i2s_sck: Optional[int] = None


class RemoteHardwareConfig(BaseModel):
    model_config = ConfigDict(extra='ignore') #, populate_by_name=True, alias_generator=to_camel
    enabled: Optional[bool] = None
    allow_undefined_pin_access: Optional[bool] = None
    available_pins: Optional[List[int]] = None


class NeighborInfoConfig(BaseModel):
    model_config = ConfigDict(extra='ignore') #, populate_by_name=True, alias_generator=to_camel
    enabled: Optional[bool] = None
    update_interval: Optional[int] = None
    transmit_over_lora: Optional[bool] = None


class AmbientLightingConfig(BaseModel):
    model_config = ConfigDict(extra='ignore') #, populate_by_name=True, alias_generator=to_camel
    led_state: Optional[bool] = None
    current: Optional[int] = None
    red: Optional[int] = None
    green: Optional[int] = None
    blue: Optional[int] = None


class DetectionSensorConfig(BaseModel):
    model_config = ConfigDict(extra='ignore') #, populate_by_name=True, alias_generator=to_camel
    minimum_broadcast_secs: Optional[int] = None
    detection_trigger_type: Optional[str] = None  # e.g. "LOGIC_HIGH"
    enabled: Optional[bool] = None
    state_broadcast_secs: Optional[int] = None
    send_bell: Optional[bool] = None
    name: Optional[str] = None
    monitor_pin: Optional[int] = None
    use_pullup: Optional[bool] = None


class PaxcounterConfig(BaseModel):
    model_config = ConfigDict(extra='ignore') #, populate_by_name=True, alias_generator=to_camel
    enabled: Optional[bool] = None
    paxcounter_update_interval: Optional[int] = None
    wifi_threshold: Optional[int] = None
    ble_threshold: Optional[int] = None


# ---------- Top-level container ----------

class ModulesConfig(BaseModel):
    """
    Container for all module configs. Accepts the exact dict emitted by Meshtastic
    (camelCase keys) thanks to alias generation. Unknown submodules/fields are ignored.
    """
    model_config = ConfigDict(extra='ignore') #, populate_by_name=True, alias_generator=to_camel

    mqtt: Optional[MQTTConfig] = None
    serial: Optional[SerialConfig] = None
    external_notification: Optional[ExternalNotificationConfig] = None
    store_forward: Optional[StoreForwardConfig] = None
    range_test: Optional[RangeTestConfig] = None
    telemetry: Optional[TelemetryConfig] = None
    canned_message: Optional[CannedMessageConfig] = None
    audio: Optional[AudioConfig] = None
    remote_hardware: Optional[RemoteHardwareConfig] = None
    neighbor_info: Optional[NeighborInfoConfig] = None
    ambient_lighting: Optional[AmbientLightingConfig] = None
    detection_sensor: Optional[DetectionSensorConfig] = None
    paxcounter: Optional[PaxcounterConfig] = None
    version: Optional[int] = None
