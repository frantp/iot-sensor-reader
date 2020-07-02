from collections import OrderedDict, deque
import json
import os
import subprocess as sp
import time
import threading

from ...core import DriverBase


EXE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "bsec_bme680")


def _pipe(fh, q):
    for line in fh:
        q.append(json.loads(line.strip(), object_pairs_hook=OrderedDict))
    fh.close()
    q.append(None)


class Driver(DriverBase):
    def __init__(self, address=0x77):
        self._queue = deque(maxlen=1)
        self._proc = sp.Popen([EXE, str(address)], text=True,
                              stdout=sp.PIPE, stderr=sp.DEVNULL)
        self._thread = threading.Thread(target=_pipe,
                                        args=(self._proc.stdout, self._queue))
        self._thread.start()

    def run(self):
        try:
            res = self._queue.popleft()
        except IndexError:
            res = None
        return [(self.sid(), time.time_ns(), res)]

    def close(self):
        self._proc.terminate()
        self._thread.join()
