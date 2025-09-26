from __future__ import annotations

from typing import Optional, List, Dict, Literal, Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
import re
import json

from models.module_config_model import ModulesConfig

_ACK_RETRIES=2
_ACK_TIMEOUT_S=10.0
_DEFAULT_PSK=b'\x01'
ROLE_NAMES={'LOST_AND_FOUND', 'CLIENT_MUTE', 'CLIENT_HIDDEN', 'REPEATER', 'ROUTER_LATE', 'ROUTER_CLIENT', 'TRACKER', 'CLIENT', 'ROUTER', 'TAK', 'TAK_TRACKER', 'SENSOR'}
REGION_NAMES={'BR_902', 'LORA_24', 'PH_915', 'EU_433', 'RU', 'MY_919', 'NP_865', 'PH_868', 'NZ_865', 'UA_433', 'UNSET', 'PH_433', 'SG_923', 'ANZ', 'KZ_433', 'TH', 'TW', 'EU_868', 'US', 'JP', 'IN', 'ANZ_433', 'CN', 'KR', 'KZ_863', 'UA_868', 'MY_433'}
MODEM_PRESET_NAMES={'MEDIUM_FAST', 'LONG_SLOW', 'MEDIUM_SLOW', 'SHORT_FAST', 'SHORT_TURBO', 'VERY_LONG_SLOW', 'LONG_FAST', 'SHORT_SLOW', 'LONG_MODERATE'}

_BASE64_RE = re.compile(r"^[A-Za-z0-9+/]+={0,2}$")
def _is_base64ish(s: str) -> bool:
    """Lightweight base64 sanity check: charset + padding + length multiple of 4."""
    if not s or not _BASE64_RE.fullmatch(s):
        return False
    return (len(s) % 4) == 0

def _err(prefix: str, detail: str) -> str:
    return f"{prefix}: {detail}"

is_cfg_reloaded=True
failures=None
user={
  "id": "!db295bf8",
  "longName": "ADMS_TEST_NODE_01",
  "shortName": "TST1",
  "macaddr": "EFHbKVv4",
  "hwModel": "HELTEC_V3",
  "role": "CLIENT_MUTE",
  "publicKey": "Kn/4Ij0qU5Apv6Sl1GuSsc5Ig4wDo1cKg6g+ITigh20="
}
class UserInfo(BaseModel):
    model_config = ConfigDict(extra='ignore')  # drop unknown keys
    id: Optional[str] = None
    longName: Optional[str] = None
    shortName: Optional[str] = None
    macaddr: Optional[str] = None
    hwModel: Optional[str] = None
    # role: Optional[str] = None # duplicate with Device. so we'll just leave it in device.
    publicKey: Optional[str] = None

metadata={
  "firmwareVersion": "2.6.11.60ec05e",
  "deviceStateVersion": 24,
  "canShutdown": True,
  "hasWifi": True,
  "hasBluetooth": True,
  "role": "CLIENT_MUTE",
  "positionFlags": 811,
  "hwModel": "HELTEC_V3",
  "hasPKC": True,
  "excludedModules": 1280,
  "hasEthernet": False,
  "hasRemoteHardware": False
}
class MetaData(BaseModel):
    model_config = ConfigDict(extra='ignore')  # drop unknown keys
    
    port: Optional[str] = None # added to metadata.
    firmwareVersion: Optional[str] = None
    deviceStateVersion: Optional[int] = None 
    canShutdown: Optional[bool] = True
    hasWifi: Optional[bool] = False
    hasBluetooth: Optional[bool] = False
    # role: Optional[str] = None # dupe, leaving in Device.
    positionFlags: Optional[int] = None
    hwModel: Optional[str] = None
    hasPKC: Optional[bool] = None
    excludedModules: Optional[int] = None
    hasEthernet: Optional[bool] = False
    hasRemoteHardware: Optional[bool] = False


my_info={
  "myNodeNum": 3676920824,
  "rebootCount": 221,
  "minAppVersion": 30200,
  "deviceId": "grXQAp1J6Uz/seGbGlH5jQ==",
  "pioEnv": "heltec-v3",
  "firmwareEdition": "VANILLA",
  "nodedbCount": 0
}
class MyInfo(BaseModel):
    model_config = ConfigDict(extra='ignore')  # drop unknown keys
    myNodeNum: Optional[int] = None
    rebootCount: Optional[int] = None
    minAppVersion: Optional[int] = None
    deviceId: Optional[str] = None
    pioEnv: Optional[str] = None
    firmwareEdition: Optional[str] = None
    nodedbCount: Optional[int] = 0


device={
    "role": "CLIENT_MUTE",
    "rebroadcastMode": "LOCAL_ONLY",
    "nodeInfoBroadcastSecs": 10800,
    "ledHeartbeatDisabled": True,
    "serialEnabled": False,
    "buttonGpio": 0,
    "buzzerGpio": 0,
    "doubleTapAsButtonPress": False,
    "isManaged": False,
    "disableTripleClick": False,
    "tzdef": "",
    "buzzerMode": "ALL_ENABLED"
}
class Device(BaseModel):
    model_config = ConfigDict(extra='ignore')  # drop unknown keys
    role: Optional[str] = "CLIENT" #
    rebroadcastMode: Optional[str] = None
    nodeInfoBroadcastSecs: Optional[int] = None
    ledHeartbeatDisabled: Optional[bool] = None
    serialEnabled: Optional[bool] = None
    buttonGpio: Optional[int] = None
    buzzerGpio: Optional[int] = None
    doubleTapAsButtonPress: Optional[bool] = None
    isManaged: Optional[bool] = None
    disableTripleClick: Optional[bool] = None
    tzdef: Optional[str] = None
    buzzerMode: Optional[str] = None

power={
    "sdsSecs": 86400,
    "lsSecs": 300,
    "minWakeSecs": 10,
    "isPowerSaving": False,
    "onBatteryShutdownAfterSecs": 0,
    "adcMultiplierOverride": 0.0,
    "waitBluetoothSecs": 0,
    "deviceBatteryInaAddress": 0,
    "powermonEnables": "0"
}
class Power(BaseModel):
    model_config = ConfigDict(extra='ignore')  # drop unknown keys
    sdsSecs: Optional[int] = 86400 # 1 day
    lsSecs: Optional[int] = 300
    minWakeSecs: Optional[int] = 10
    isPowerSaving: Optional[bool] = False
    onBatteryShutdownAfterSecs: Optional[int] = None
    adcMultiplierOverride: Optional[float] = None
    waitBluetoothSecs: Optional[int] = None
    deviceBatteryInaAddress: Optional[int] = None
    powermonEnables: Optional[str] = None
    

lora={
  "usePreset": True,
  "region": "US",
  "hopLimit": 3,
  "txEnabled": True,
  "txPower": 22,
  "channelNum": 55,
  "sx126xRxBoostedGain": True,
  "modemPreset": "LONG_FAST",
  "bandwidth": 0,
  "spreadFactor": 0,
  "codingRate": 0,
  "frequencyOffset": 0.0,
  "overrideDutyCycle": False,
  "overrideFrequency": 0.0,
  "paFanDisabled": False,
  "ignoreIncoming": [],
  "ignoreMqtt": False,
  "configOkToMqtt": False
}
class Lora(BaseModel):
    model_config = ConfigDict(extra='ignore')  # drop unknown keys
    usePreset: Optional[bool] = True
    region: Optional[str] = None
    hopLimit: Optional[int] = None
    txEnabled: Optional[bool] = True
    txPower: Optional[int] = None
    channelNum: Optional[int] = 20
    sx126xRxBoostedGain: Optional[bool] = True
    modemPreset: Optional[str] = None
    bandwidth: Optional[int] = None
    spreadFactor: Optional[int] = None
    codingRate: Optional[int] = None
    frequencyOffset: Optional[float] = None
    overrideDutyCycle: Optional[bool] = None
    overrideFrequency: Optional[float] = None
    paFanDisabled: Optional[bool] = None
    ignoreIncoming: Optional[List] = []
    ignoreMqtt: Optional[bool] = None
    configOkToMqtt: Optional[int] = None


position={
    "positionBroadcastSecs": 43200,
    "positionBroadcastSmartEnabled": True,
    "gpsUpdateInterval": 86400,
    "positionFlags": 811,
    "broadcastSmartMinimumDistance": 100,
    "broadcastSmartMinimumIntervalSecs": 30,
    "gpsMode": "NOT_PRESENT",
    "fixedPosition": False,
    "gpsEnabled": False,
    "gpsAttemptTime": 0,
    "rxGpio": 0,
    "txGpio": 0,
    "gpsEnGpio": 0
}
class Position(BaseModel):
    model_config = ConfigDict(extra='ignore')  # drop unknown keys
    positionBroadcastSecs: Optional[int] = 43200 # 12 hours
    positionBroadcastSmartEnabled: Optional[bool] = True
    gpsUpdateInterval: Optional[int] = 86400 # 24 hours
    positionFlags: Optional[int] = None
    broadcastSmartMinimumDistance: Optional[int] = 100 # meters
    broadcastSmartMinimumIntervalSecs: Optional[int] = 30
    gpsMode: Optional[str] = None
    fixedPosition: Optional[bool] = None
    gpsEnabled: Optional[bool] = None
    gpsAttemptTime: Optional[int] = None
    rxGpio: Optional[int] = None
    txGpio: Optional[int] = None
    gpsEnGpio: Optional[int] = None


display={
    "screenOnSecs": 1,
    "gpsFormat": "DEC",
    "autoScreenCarouselSecs": 0,
    "compassNorthTop": False,
    "flipScreen": False,
    "units": "METRIC",
    "oled": "OLED_AUTO",
    "displaymode": "DEFAULT",
    "headingBold": False,
    "wakeOnTapOrMotion": False,
    "compassOrientation": "DEGREES_0",
    "use12hClock": False
}
class Display(BaseModel):
    model_config = ConfigDict(extra='ignore')  # drop unknown keys
    screenOnSecs: Optional[int] = 3
    gpsFormat: Optional[str] = None
    autoScreenCarouselSecs: Optional[int] = 0
    compassNorthTop: Optional[bool] = None
    flipScreen: Optional[bool] = None
    units: Optional[str] = None
    oled: Optional[str] = None
    displaymode: Optional[str] = None
    headingBold: Optional[bool] = None
    wakeOnTapOrMotion: Optional[bool] = None
    compassOrientation: Optional[str] = None
    use12hClock: Optional[bool] = None



bluetooth={
  "fixedPin": 123456,
  "enabled": False,
  "mode": "RANDOM_PIN"
}
class BlueTooth(BaseModel): # might want to not ignore extras for bt.
    model_config = ConfigDict(extra='ignore')  # drop unknown keys
    fixedPin: Optional[int] = None
    enabled: Optional[bool] = None
    mode: Optional[str] = None

network={
    "ntpServer": "meshtastic.pool.ntp.org",
    "enabledProtocols": 1,
    "wifiEnabled": False,
    "wifiSsid": "",
    "wifiPsk": "",
    "ethEnabled": False,
    "addressMode": "DHCP",
    "rsyslogServer": "",
    "ipv6Enabled": False
}
class Network(BaseModel):
    model_config = ConfigDict(extra='ignore')  # drop unknown keys
    ntpServer: Optional[str] = None
    enabledProtocols: Optional[int] = None
    wifiEnabled: Optional[bool] = None
    wifiSsid: Optional[str] = None
    wifiPsk: Optional[str] = None
    ethEnabled: Optional[bool] = None
    addressMode: Optional[str] = None
    rsyslogServer: Optional[str] = None
    ipv6Enabled: Optional[bool] = None



mesh_channels=[
    {
    "index": 0,
    "name": "localnet-30",
    "uplink_enabled": False,
    "downlink_enabled": False,
    "position_precision": 32,
    "psk": "RySCKAybPsBEVVZFj/x9NIhzub1L683th6Nh6bnzeMU=",
    "psk_present": True,
    "role": None
    },
    {
    "index": 1,
    "name": "LongFast",
    "uplink_enabled": False,
    "downlink_enabled": False,
    "position_precision": 0,
    "psk_present": False,
    "psk_strategy": "leave",
    "key_explicit_b64": "AQ==",
    "role": None
    }
]

class MeshChannel(BaseModel):
    """
    Canonical channel representation with PSK masking semantics.
    - Never decode PSKs here. Validation is structural only.
    """
    index: int
    name: Optional[str] = None
    uplink_enabled: Optional[bool] = None
    downlink_enabled: Optional[bool] = None

    # 0..32 (Meshtastic GPS position precision bits; 0 disables GPS sharing on channel)
    position_precision: int = 0

    # PSK handling/visibility flags (never store secrets in GUI paths)
    psk: Optional[str]=None
    psk_present: bool = False
    
    # Optional per-channel logical role (validated against ROLE_NAMES if provided)
    role: Optional[str] = None

    # ---- Derived ----
    @property
    def is_gps_enabled(self) -> bool:
        return self.position_precision > 0

    # ---- Validators ----
    @field_validator("index")
    @classmethod
    def _v_index(cls, v: int) -> int:
        if v < 0:
            raise ValueError(_err("channel.index", "must be >= 0"))
        return v

    @field_validator("position_precision")
    @classmethod
    def _v_position_precision(cls, v: int) -> int:
        if not (0 <= v <= 32):
            raise ValueError(_err("channel.position_precision", "must be in [0, 32]"))
        return v



class DeviceModel(BaseModel):
    UserInfo: Optional[UserInfo]
    MetaData: Optional[MetaData]
    MyInfo: Optional[MyInfo]
    Device: Optional[Device]
    Power: Optional[Power]
    Lora: Optional[Lora]
    Position: Optional[Position]
    Display: Optional[Display]
    BlueTooth: Optional[BlueTooth]
    Network: Optional[Network]
    MeshChannels: List[MeshChannel]
    ModuleConfig: Optional[ModulesConfig]