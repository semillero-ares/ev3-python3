"""
LEGO Mindstorms EV3 direct commands - UART Sensor Class
"""

import struct
from .ev3 import EV3
from .constants import (
    PORT_1,
    PORT_2,
    PORT_3,
    PORT_4,
    opInput_Device,
    READY_RAW,
)
from .functions import LCX, GVX
from .exceptions import SensorError, PortInUse


class UART(EV3):
    """
    controls a single UART sensor 
    """

    def __init__(
            self,
            port: bytes,
            *,
            protocol: str = None,
            host: str = None,
            ev3_obj: EV3 = None,
            verbosity=0
    ):
        """
        Positional Arguments

          port
            port of UART sensor (PORT_1, PORT_2, PORT_3 or PORT_4)

        Keyword only Arguments (either protocol and host or ev3_obj)

          protocol
            either ev3_dc.BLUETOOTH, ev3_dc.USB or ev3_dc.WIFI
          host
            mac-address of the LEGO EV3 (e.g. '00:16:53:42:2B:99')
          ev3_obj
            an existing EV3 object 
            (its already established connection will be used)
          verbosity
            level (0, 1, 2) of verbosity (prints on stdout).
        """
        assert port in (PORT_1, PORT_2, PORT_3, PORT_4), "incorrect port"
        self._port = port

        super().__init__(
            protocol=protocol,
            host=host,
            ev3_obj=ev3_obj,
            verbosity=verbosity
        )

        if self._physical_ev3._introspection is None:
            self._physical_ev3.introspection(verbosity)

        if self._physical_ev3._introspection["sensors"][self._port]['used_by'] is not None:
            port_str = 'PORT_' + str(1 + struct.unpack("<B", self._port)[0])
            host_str = self._physical_ev3._host
            raise PortInUse(f'{port_str} of {host_str} already in use')

    def __str__(self):
        """description of the object in a str context"""
        type_str = ('EV3_UART')
        port_str = 'PORT_' + str(1 + struct.unpack("<B", self._port)[0])
        return ' '.join((
            type_str,
            f'at {port_str}',
            f'of {super().__str__()}'
        ))

    def __del__(self):
        """
        handle specific logic for deletion
        """
        if self._physical_ev3 is not None:
            self._physical_ev3._introspection["sensors"][self._port]['used_by'] = None
            super().__del__()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """
        handle specific logic when exit with block
        """
        self._physical_ev3._introspection["sensors"][self._port]['used_by'] = None
        super().__exit__(exc_type, exc_value, exc_traceback)

    @property
    def port(self) -> bytes:
        """
        port, where sensor is connected (PORT_1, PORT_2, PORT_3 or PORT_4)
        """
        return self._port

    @property
    def sensor_type(self) -> int:
        """
        type of sensor
        """
        return self.sensors_as_dict[self._port]

    @property
    def value(self) -> float:
        """
        gets the raw value from the sensor
        """

        reply = self.send_direct_cmd(
            b''.join((
                opInput_Device,     # operation
                READY_RAW,          # CMD
                LCX(0),             # LAYER
                self._port,         # NO
                LCX(5),             # TYPE
                LCX(0),             # MODE (cm)
                LCX(1),             # VALUES
                GVX(0)              # VALUE1 (output)
            )),
            global_mem=4
        )
        val = struct.unpack('<i', reply)[0]
        return float(val)
