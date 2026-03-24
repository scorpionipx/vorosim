import ctypes
import mmap
import sys
from ctypes import wintypes


# ============================================================
# Assetto Corsa shared memory pages
# ============================================================

class SPageFilePhysics(ctypes.Structure):
    _fields_ = [
        ("packetId", ctypes.c_int),
        ("gas", ctypes.c_float),
        ("brake", ctypes.c_float),
        ("fuel", ctypes.c_float),
        ("gear", ctypes.c_int),
        ("rpms", ctypes.c_int),
        ("steerAngle", ctypes.c_float),
        ("speedKmh", ctypes.c_float),
        ("velocity", ctypes.c_float * 3),
        ("accG", ctypes.c_float * 3),
        ("wheelSlip", ctypes.c_float * 4),
        ("wheelLoad", ctypes.c_float * 4),
        ("wheelsPressure", ctypes.c_float * 4),
        ("wheelAngularSpeed", ctypes.c_float * 4),
        ("tyreWear", ctypes.c_float * 4),
        ("tyreDirtyLevel", ctypes.c_float * 4),
        ("tyreCoreTemperature", ctypes.c_float * 4),
        ("camberRAD", ctypes.c_float * 4),
        ("suspensionTravel", ctypes.c_float * 4),
        ("drs", ctypes.c_float),
        ("tc", ctypes.c_float),
        ("heading", ctypes.c_float),
        ("pitch", ctypes.c_float),
        ("roll", ctypes.c_float),
        ("cgHeight", ctypes.c_float),
        ("carDamage", ctypes.c_float * 5),
        ("numberOfTyresOut", ctypes.c_int),
        ("pitLimiterOn", ctypes.c_int),
        ("abs", ctypes.c_float),
        ("kersCharge", ctypes.c_float),
        ("kersInput", ctypes.c_float),
        ("autoShifterOn", ctypes.c_int),
        ("rideHeight", ctypes.c_float * 2),
        ("turboBoost", ctypes.c_float),
        ("ballast", ctypes.c_float),
        ("airDensity", ctypes.c_float),
        ("airTemp", ctypes.c_float),
        ("roadTemp", ctypes.c_float),
        ("localAngularVel", ctypes.c_float * 3),
        ("finalFF", ctypes.c_float),
        ("performanceMeter", ctypes.c_float),
        ("engineBrake", ctypes.c_int),
        ("ersRecoveryLevel", ctypes.c_int),
        ("ersPowerLevel", ctypes.c_int),
        ("ersHeatCharging", ctypes.c_int),
        ("ersIsCharging", ctypes.c_int),
        ("kersCurrentKJ", ctypes.c_float),
        ("drsAvailable", ctypes.c_int),
        ("drsEnabled", ctypes.c_int),
        ("brakeTemp", ctypes.c_float * 4),
        ("clutch", ctypes.c_float),
        ("tyreTempI", ctypes.c_float * 4),
        ("tyreTempM", ctypes.c_float * 4),
        ("tyreTempO", ctypes.c_float * 4),
        ("isAIControlled", ctypes.c_int),
        ("tyreContactPoint", (ctypes.c_float * 3) * 4),
        ("tyreContactNormal", (ctypes.c_float * 3) * 4),
        ("tyreContactHeading", (ctypes.c_float * 3) * 4),
        ("brakeBias", ctypes.c_float),
        ("localVelocity", ctypes.c_float * 3),
        ("P2PActivation", ctypes.c_int),
        ("P2PStatus", ctypes.c_int),
        ("currentMaxRpm", ctypes.c_float),
        ("mz", ctypes.c_float * 4),
        ("fx", ctypes.c_float * 4),
        ("fy", ctypes.c_float * 4),
        ("slipRatio", ctypes.c_float * 4),
        ("slipAngle", ctypes.c_float * 4),
        ("tcInAction", ctypes.c_int),
        ("absInAction", ctypes.c_int),
        ("suspensionDamage", ctypes.c_float * 4),
        ("tyreTemp", ctypes.c_float * 4),
        ("waterTemp", ctypes.c_float),
        ("brakePressure", ctypes.c_float * 4),
        ("frontBrakeCompound", ctypes.c_int),
        ("rearBrakeCompound", ctypes.c_int),
        ("padLife", ctypes.c_float * 4),
        ("discLife", ctypes.c_float * 4),
        ("ignitionOn", ctypes.c_int),
        ("starterEngineOn", ctypes.c_int),
        ("isEngineRunning", ctypes.c_int),
        ("kerbVibration", ctypes.c_float),
        ("slipVibrations", ctypes.c_float),
        ("gVibrations", ctypes.c_float),
        ("absVibrations", ctypes.c_float),
    ]


class SPageFileGraphic(ctypes.Structure):
    _fields_ = [
        ("packetId", ctypes.c_int),
        ("status", ctypes.c_int),
        ("session", ctypes.c_int),
        ("currentTime", ctypes.c_wchar * 15),
        ("lastTime", ctypes.c_wchar * 15),
        ("bestTime", ctypes.c_wchar * 15),
        ("split", ctypes.c_wchar * 15),
        ("completedLaps", ctypes.c_int),
        ("position", ctypes.c_int),
        ("iCurrentTime", ctypes.c_int),
        ("iLastTime", ctypes.c_int),
        ("iBestTime", ctypes.c_int),
        ("sessionTimeLeft", ctypes.c_float),
        ("distanceTraveled", ctypes.c_float),
        ("isInPit", ctypes.c_int),
        ("currentSectorIndex", ctypes.c_int),
        ("lastSectorTime", ctypes.c_int),
        ("numberOfLaps", ctypes.c_int),
        ("tyreCompound", ctypes.c_wchar * 33),
        ("replayTimeMultiplier", ctypes.c_float),
        ("normalizedCarPosition", ctypes.c_float),
        ("activeCars", ctypes.c_int),
        ("carCoordinates", (ctypes.c_float * 3) * 60),
        ("carID", ctypes.c_int * 60),
        ("playerCarID", ctypes.c_int),
        ("penaltyTime", ctypes.c_float),
        ("flag", ctypes.c_int),
        ("idealLineOn", ctypes.c_int),
        ("isInPitLane", ctypes.c_int),
        ("surfaceGrip", ctypes.c_float),
        ("mandatoryPitDone", ctypes.c_int),
        ("windSpeed", ctypes.c_float),
        ("windDirection", ctypes.c_float),
        ("isSetupMenuVisible", ctypes.c_int),
        ("mainDisplayIndex", ctypes.c_int),
        ("secondaryDisplayIndex", ctypes.c_int),
        ("TC", ctypes.c_int),
        ("TCCut", ctypes.c_int),
        ("EngineMap", ctypes.c_int),
        ("ABS", ctypes.c_int),
        ("fuelXLap", ctypes.c_float),
        ("rainLights", ctypes.c_int),
        ("flashingLights", ctypes.c_int),
        ("lightsStage", ctypes.c_int),
        ("exhaustTemperature", ctypes.c_float),
        ("wiperLV", ctypes.c_int),
        ("driverStintTotalTimeLeft", ctypes.c_int),
        ("driverStintTimeLeft", ctypes.c_int),
        ("rainTyres", ctypes.c_int),
        ("sessionIndex", ctypes.c_int),
        ("usedFuel", ctypes.c_float),
        ("deltaLapTime", ctypes.c_wchar * 15),
        ("iDeltaLapTime", ctypes.c_int),
        ("estimatedLapTime", ctypes.c_wchar * 15),
        ("iEstimatedLapTime", ctypes.c_int),
        ("isDeltaPositive", ctypes.c_int),
        ("iSplit", ctypes.c_int),
        ("isValidLap", ctypes.c_int),
        ("fuelEstimatedLaps", ctypes.c_float),
        ("trackStatus", ctypes.c_wchar * 33),
        ("missingMandatoryPits", ctypes.c_int),
        ("Clock", ctypes.c_float),
        ("directionLightsLeft", ctypes.c_int),
        ("directionLightsRight", ctypes.c_int),
        ("GlobalYellow", ctypes.c_int),
        ("GlobalYellow1", ctypes.c_int),
        ("GlobalYellow2", ctypes.c_int),
        ("GlobalYellow3", ctypes.c_int),
        ("GlobalWhite", ctypes.c_int),
        ("GlobalGreen", ctypes.c_int),
        ("GlobalChequered", ctypes.c_int),
        ("GlobalRed", ctypes.c_int),
        ("mfdTyreSet", ctypes.c_int),
        ("mfdFuelToAdd", ctypes.c_float),
        ("mfdTyrePressureLF", ctypes.c_float),
        ("mfdTyrePressureRF", ctypes.c_float),
        ("mfdTyrePressureLR", ctypes.c_float),
        ("mfdTyrePressureRR", ctypes.c_float),
        ("trackGripStatus", ctypes.c_wchar * 33),
        ("rainIntensity", ctypes.c_int),
        ("rainIntensityIn10min", ctypes.c_int),
        ("rainIntensityIn30min", ctypes.c_int),
        ("currentTyreSet", ctypes.c_int),
        ("strategyTyreSet", ctypes.c_int),
    ]


class SPageFileStatic(ctypes.Structure):
    _fields_ = [
        ("smVersion", ctypes.c_wchar * 15),
        ("acVersion", ctypes.c_wchar * 15),
        ("numberOfSessions", ctypes.c_int),
        ("numCars", ctypes.c_int),
        ("carModel", ctypes.c_wchar * 33),
        ("track", ctypes.c_wchar * 33),
        ("playerName", ctypes.c_wchar * 33),
        ("playerSurname", ctypes.c_wchar * 33),
        ("playerNick", ctypes.c_wchar * 33),
        ("sectorCount", ctypes.c_int),
        ("maxTorque", ctypes.c_float),
        ("maxPower", ctypes.c_float),
        ("maxRpm", ctypes.c_int),
        ("maxFuel", ctypes.c_float),
        ("suspensionMaxTravel", ctypes.c_float * 4),
        ("tyreRadius", ctypes.c_float * 4),
        ("maxTurboBoost", ctypes.c_float),
        ("deprecated_1", ctypes.c_float),
        ("deprecated_2", ctypes.c_float),
        ("penaltiesEnabled", ctypes.c_int),
        ("aidFuelRate", ctypes.c_float),
        ("aidTireRate", ctypes.c_float),
        ("aidMechanicalDamage", ctypes.c_float),
        ("aidAllowTyreBlankets", ctypes.c_int),
        ("aidStability", ctypes.c_float),
        ("aidAutoClutch", ctypes.c_int),
        ("aidAutoBlip", ctypes.c_int),
        ("hasDRS", ctypes.c_int),
        ("hasERS", ctypes.c_int),
        ("hasKERS", ctypes.c_int),
        ("kersMaxJ", ctypes.c_float),
        ("engineBrakeSettingsCount", ctypes.c_int),
        ("ersPowerControllerCount", ctypes.c_int),
        ("trackSPlineLength", ctypes.c_float),
        ("trackConfiguration", ctypes.c_wchar * 33),
        ("ersMaxJ", ctypes.c_float),
        ("isTimedRace", ctypes.c_int),
        ("hasExtraLap", ctypes.c_int),
        ("carSkin", ctypes.c_wchar * 33),
        ("reversedGridPositions", ctypes.c_int),
        ("pitWindowStart", ctypes.c_int),
        ("pitWindowEnd", ctypes.c_int),
        ("isOnline", ctypes.c_int),
        ("dryTyresName", ctypes.c_wchar * 33),
        ("wetTyresName", ctypes.c_wchar * 33),
    ]


# ============================================================
# Shared memory reader
# ============================================================

class AssettoCorsaSharedMemory:
    """
    Windows-only reader for Assetto Corsa shared memory.

    Maps:
      - acpmf_physics
      - acpmf_graphics
      - acpmf_static
    """

    PHYSICS_TAG = "acpmf_physics"
    GRAPHICS_TAG = "acpmf_graphics"
    STATIC_TAG = "acpmf_static"

    def __init__(self):
        self._physics_map = None
        self._graphics_map = None
        self._static_map = None
        self._opened = False

    def open(self):
        if sys.platform != "win32":
            raise RuntimeError("Assetto Corsa shared memory is only available on Windows.")

        if self._opened:
            return

        self._physics_map = self._open_named_map(self.PHYSICS_TAG, ctypes.sizeof(SPageFilePhysics))
        self._graphics_map = self._open_named_map(self.GRAPHICS_TAG, ctypes.sizeof(SPageFileGraphic))
        self._static_map = self._open_named_map(self.STATIC_TAG, ctypes.sizeof(SPageFileStatic))
        self._opened = True

    def close(self):
        for mm in (self._physics_map, self._graphics_map, self._static_map):
            if mm is not None:
                try:
                    mm.close()
                except Exception:
                    pass

        self._physics_map = None
        self._graphics_map = None
        self._static_map = None
        self._opened = False

    def is_open(self) -> bool:
        return self._opened

    def read(self) -> dict:
        if not self._opened:
            raise RuntimeError("Shared memory not opened.")

        physics = self._read_struct(self._physics_map, SPageFilePhysics)
        graphics = self._read_struct(self._graphics_map, SPageFileGraphic)
        static = self._read_struct(self._static_map, SPageFileStatic)

        return {
            "physics": {
                "packetId": physics.packetId,
                "gas": physics.gas,
                "brake": physics.brake,
                "fuel": physics.fuel,
                "gear": physics.gear,
                "rpms": physics.rpms,
                "steerAngle": physics.steerAngle,
                "speedKmh": physics.speedKmh,
                "velocity": list(physics.velocity),
                "accG": list(physics.accG),
                "wheelSlip": list(physics.wheelSlip),
                "wheelLoad": list(physics.wheelLoad),
                "wheelsPressure": list(physics.wheelsPressure),
                "wheelAngularSpeed": list(physics.wheelAngularSpeed),
                "tyreWear": list(physics.tyreWear),
                "tyreCoreTemperature": list(physics.tyreCoreTemperature),
                "camberRAD": list(physics.camberRAD),
                "suspensionTravel": list(physics.suspensionTravel),
                "drs": physics.drs,
                "tc": physics.tc,
                "heading": physics.heading,
                "pitch": physics.pitch,
                "roll": physics.roll,
                "cgHeight": physics.cgHeight,
                "carDamage": list(physics.carDamage),
                "numberOfTyresOut": physics.numberOfTyresOut,
                "pitLimiterOn": bool(physics.pitLimiterOn),
                "abs": physics.abs,
                "kersCharge": physics.kersCharge,
                "kersInput": physics.kersInput,
                "autoShifterOn": bool(physics.autoShifterOn),
                "rideHeight": list(physics.rideHeight),
                "turboBoost": physics.turboBoost,
                "airTemp": physics.airTemp,
                "roadTemp": physics.roadTemp,
                "localAngularVel": list(physics.localAngularVel),
                "finalFF": physics.finalFF,
                "performanceMeter": physics.performanceMeter,
                "engineBrake": physics.engineBrake,
                "ersRecoveryLevel": physics.ersRecoveryLevel,
                "ersPowerLevel": physics.ersPowerLevel,
                "ersHeatCharging": bool(physics.ersHeatCharging),
                "ersIsCharging": bool(physics.ersIsCharging),
                "kersCurrentKJ": physics.kersCurrentKJ,
                "drsAvailable": bool(physics.drsAvailable),
                "drsEnabled": bool(physics.drsEnabled),
                "brakeTemp": list(physics.brakeTemp),
                "clutch": physics.clutch,
                "tyreTempI": list(physics.tyreTempI),
                "tyreTempM": list(physics.tyreTempM),
                "tyreTempO": list(physics.tyreTempO),
                "isAIControlled": bool(physics.isAIControlled),
                "brakeBias": physics.brakeBias,
                "localVelocity": list(physics.localVelocity),
                "P2PActivation": bool(physics.P2PActivation),
                "P2PStatus": bool(physics.P2PStatus),
                "currentMaxRpm": physics.currentMaxRpm,
                "mz": list(physics.mz),
                "fx": list(physics.fx),
                "fy": list(physics.fy),
                "slipRatio": list(physics.slipRatio),
                "slipAngle": list(physics.slipAngle),
                "tcInAction": bool(physics.tcInAction),
                "absInAction": bool(physics.absInAction),
                "suspensionDamage": list(physics.suspensionDamage),
                "tyreTemp": list(physics.tyreTemp),
                "waterTemp": physics.waterTemp,
                "brakePressure": list(physics.brakePressure),
                "frontBrakeCompound": physics.frontBrakeCompound,
                "rearBrakeCompound": physics.rearBrakeCompound,
                "padLife": list(physics.padLife),
                "discLife": list(physics.discLife),
                "ignitionOn": bool(physics.ignitionOn),
                "starterEngineOn": bool(physics.starterEngineOn),
                "isEngineRunning": bool(physics.isEngineRunning),
                "kerbVibration": physics.kerbVibration,
                "slipVibrations": physics.slipVibrations,
                "gVibrations": physics.gVibrations,
                "absVibrations": physics.absVibrations,
            },
            "graphics": {
                "packetId": graphics.packetId,
                "status": graphics.status,
                "session": graphics.session,
                "currentTime": graphics.currentTime.rstrip("\x00"),
                "lastTime": graphics.lastTime.rstrip("\x00"),
                "bestTime": graphics.bestTime.rstrip("\x00"),
                "split": graphics.split.rstrip("\x00"),
                "completedLaps": graphics.completedLaps,
                "position": graphics.position,
                "iCurrentTime": graphics.iCurrentTime,
                "iLastTime": graphics.iLastTime,
                "iBestTime": graphics.iBestTime,
                "sessionTimeLeft": graphics.sessionTimeLeft,
                "distanceTraveled": graphics.distanceTraveled,
                "isInPit": bool(graphics.isInPit),
                "currentSectorIndex": graphics.currentSectorIndex,
                "lastSectorTime": graphics.lastSectorTime,
                "numberOfLaps": graphics.numberOfLaps,
                "tyreCompound": graphics.tyreCompound.rstrip("\x00"),
                "normalizedCarPosition": graphics.normalizedCarPosition,
                "activeCars": graphics.activeCars,
                "playerCarID": graphics.playerCarID,
                "penaltyTime": graphics.penaltyTime,
                "flag": graphics.flag,
                "idealLineOn": bool(graphics.idealLineOn),
                "isInPitLane": bool(graphics.isInPitLane),
                "surfaceGrip": graphics.surfaceGrip,
                "mandatoryPitDone": bool(graphics.mandatoryPitDone),
                "windSpeed": graphics.windSpeed,
                "windDirection": graphics.windDirection,
                "isSetupMenuVisible": bool(graphics.isSetupMenuVisible),
                "TC": graphics.TC,
                "TCCut": graphics.TCCut,
                "EngineMap": graphics.EngineMap,
                "ABS": graphics.ABS,
                "fuelXLap": graphics.fuelXLap,
                "rainLights": bool(graphics.rainLights),
                "flashingLights": bool(graphics.flashingLights),
                "lightsStage": graphics.lightsStage,
                "exhaustTemperature": graphics.exhaustTemperature,
                "wiperLV": graphics.wiperLV,
                "usedFuel": graphics.usedFuel,
                "deltaLapTime": graphics.deltaLapTime.rstrip("\x00"),
                "iDeltaLapTime": graphics.iDeltaLapTime,
                "estimatedLapTime": graphics.estimatedLapTime.rstrip("\x00"),
                "iEstimatedLapTime": graphics.iEstimatedLapTime,
                "isDeltaPositive": bool(graphics.isDeltaPositive),
                "iSplit": graphics.iSplit,
                "isValidLap": bool(graphics.isValidLap),
                "fuelEstimatedLaps": graphics.fuelEstimatedLaps,
                "trackStatus": graphics.trackStatus.rstrip("\x00"),
                "Clock": graphics.Clock,
                "trackGripStatus": graphics.trackGripStatus.rstrip("\x00"),
                "rainIntensity": graphics.rainIntensity,
                "rainIntensityIn10min": graphics.rainIntensityIn10min,
                "rainIntensityIn30min": graphics.rainIntensityIn30min,
                "currentTyreSet": graphics.currentTyreSet,
                "strategyTyreSet": graphics.strategyTyreSet,
            },
            "static": {
                "smVersion": static.smVersion.rstrip("\x00"),
                "acVersion": static.acVersion.rstrip("\x00"),
                "numberOfSessions": static.numberOfSessions,
                "numCars": static.numCars,
                "carModel": static.carModel.rstrip("\x00"),
                "track": static.track.rstrip("\x00"),
                "playerName": static.playerName.rstrip("\x00"),
                "playerSurname": static.playerSurname.rstrip("\x00"),
                "playerNick": static.playerNick.rstrip("\x00"),
                "sectorCount": static.sectorCount,
                "maxTorque": static.maxTorque,
                "maxPower": static.maxPower,
                "maxRpm": static.maxRpm,
                "maxFuel": static.maxFuel,
                "suspensionMaxTravel": list(static.suspensionMaxTravel),
                "tyreRadius": list(static.tyreRadius),
                "maxTurboBoost": static.maxTurboBoost,
                "penaltiesEnabled": bool(static.penaltiesEnabled),
                "aidFuelRate": static.aidFuelRate,
                "aidTireRate": static.aidTireRate,
                "aidMechanicalDamage": static.aidMechanicalDamage,
                "aidAllowTyreBlankets": bool(static.aidAllowTyreBlankets),
                "aidStability": static.aidStability,
                "aidAutoClutch": bool(static.aidAutoClutch),
                "aidAutoBlip": bool(static.aidAutoBlip),
                "hasDRS": bool(static.hasDRS),
                "hasERS": bool(static.hasERS),
                "hasKERS": bool(static.hasKERS),
                "kersMaxJ": static.kersMaxJ,
                "engineBrakeSettingsCount": static.engineBrakeSettingsCount,
                "ersPowerControllerCount": static.ersPowerControllerCount,
                "trackSPlineLength": static.trackSPlineLength,
                "trackConfiguration": static.trackConfiguration.rstrip("\x00"),
                "ersMaxJ": static.ersMaxJ,
                "isTimedRace": bool(static.isTimedRace),
                "hasExtraLap": bool(static.hasExtraLap),
                "carSkin": static.carSkin.rstrip("\x00"),
                "reversedGridPositions": static.reversedGridPositions,
                "pitWindowStart": static.pitWindowStart,
                "pitWindowEnd": static.pitWindowEnd,
                "isOnline": bool(static.isOnline),
                "dryTyresName": static.dryTyresName.rstrip("\x00"),
                "wetTyresName": static.wetTyresName.rstrip("\x00"),
            },
        }

    @staticmethod
    def _open_named_map(tagname: str, size: int) -> mmap.mmap:
        try:
            return mmap.mmap(-1, size, tagname=tagname, access=mmap.ACCESS_READ)
        except Exception as e:
            raise RuntimeError(
                f"Could not open Assetto Corsa shared memory '{tagname}'. "
                f"Is the game running? Original error: {e}"
            ) from e

    @staticmethod
    def _read_struct(mm: mmap.mmap, struct_type):
        mm.seek(0)
        raw = mm.read(ctypes.sizeof(struct_type))
        if len(raw) != ctypes.sizeof(struct_type):
            raise RuntimeError(f"Short read for {struct_type.__name__}")
        return struct_type.from_buffer_copy(raw)