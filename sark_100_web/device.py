import logging

from contextlib import closing
import serial


logger = logging.getLogger(__name__)


MAXIMUM_FREQUENCY = 60000000


class DeviceError(Exception):
    pass


def _limit_frequency(v):
    if v > MAXIMUM_FREQUENCY:
        return MAXIMUM_FREQUENCY
    return v


def get_connection(port):
    return serial.Serial(
        port=port,
        baudrate=57600,
        timeout=1,
        rtscts=True,
    )


def scan_range(port, start, stop, step):
    samples = []

    with closing(get_connection(port)) as conn:
        command = b'scan {start} {stop} {step}\r'.format(
            start=_limit_frequency(start),
            stop=_limit_frequency(stop) + step,
            step=step,
        )
        logger.info(command)
        conn.write(command)
        curr = start
        while True:
            line = conn.readline().strip()
            logger.info(line)
            if not line:
                continue
            if line == 'Start':
                continue
            if line == 'End':
                break
            if line.startswith('Error:'):
                raise DeviceError(line[6:])

            swr, r, x, z = line.split(',')
            samples.append(
                {
                    'frequency': curr,
                    'swr': float(swr),
                    'r': int(r),
                    'x': int(x),
                    'z': int(z),
                }
            )
            curr = curr + step

        # Stop the scanner
        conn.write('off\r')
        while True:
            line = conn.readline().strip()
            logger.info(line)
            if not line:
                continue
            if line == '>>':
                break
            if line == 'OK':
                break
            if line.startswith('Error:'):
                raise DeviceError(line[6:])
            else:
                raise DeviceError("Unexpected response: %s" % line)

    return samples


