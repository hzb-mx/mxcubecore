import socket
import contextlib
from typing import Optional, Tuple, List

class MD2ExporterClient:
    """Minimal socket client for the MD2 Exporter protocol.

    Notes
    -----
    This is a diagnostic / migration helper, not a full protocol implementation.
    The existing Qt4 integration uses "exporter" channels/commands already.
    This client allows raw connectivity validation and simple textual queries
    where the protocol returns newline or semicolon separated key=value pairs.

    The real production implementation should replace ad-hoc parsing with a
    structured decoder based on official MD2 Exporter documentation.
    """

    def __init__(self, host: str, port: int = 9001, timeout: float = 2.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock: Optional[socket.socket] = None

    def connect(self) -> None:
        if self._sock:
            return
        s = socket.create_connection((self.host, self.port), timeout=self.timeout)
        s.settimeout(self.timeout)
        self._sock = s

    def close(self) -> None:
        if self._sock:
            with contextlib.suppress(Exception):
                self._sock.close()
        self._sock = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def send_raw(self, data: str) -> None:
        if not self._sock:
            raise RuntimeError("Not connected")
        # Protocol may expect trailing newline
        payload = data if data.endswith("\n") else data + "\n"
        self._sock.sendall(payload.encode("utf-8"))

    def recv_raw(self, bufsize: int = 4096) -> str:
        if not self._sock:
            raise RuntimeError("Not connected")
        data = self._sock.recv(bufsize).decode("utf-8", errors="replace")
        # Strip control characters (STX=0x02, ETX=0x03)
        return data.strip("\x02\x03")

    def query(self, command: str) -> str:
        self.send_raw(command)
        return self.recv_raw()

    # Heuristic helpers (speculative, adjust when protocol specifics known)
    def get_state(self) -> str:
        """Query exporter state. Returns parsed state string."""
        response = self.query("State")
        # Response format: EVT:State\tReady\ttimestamp\torg.embl.State
        parts = response.split("\t")
        if len(parts) >= 2:
            return parts[1]  # e.g., "Ready"
        return response

    def get_motor_states(self) -> List[str]:
        """Attempt to retrieve motor states if exporter supports a 'MotorStates' command.
        Returns raw tokens list like ['Omega=Ready','SampX=Moving'] when available.
        """
        response = self.query("MotorStates")
        return [tok.strip() for tok in response.strip().split(";") if tok.strip()]

    def get_beam_position(self) -> Optional[Tuple[float, float]]:
        """Attempt to retrieve beam position via two separate commands or a combined one.
        Tries 'BeamPositionHorizontal' and 'BeamPositionVertical'. If response parsing fails
        returns None.
        """
        try:
            x_raw = self.query("BeamPositionHorizontal").strip().split()[0]
            y_raw = self.query("BeamPositionVertical").strip().split()[0]
            return float(x_raw), float(y_raw)
        except Exception:
            return None

if __name__ == "__main__":
    import sys
    host = sys.argv[1] if len(sys.argv) > 1 else "172.31.212.130"
    with MD2ExporterClient(host) as client:
        print("Connected to", host)
        print("State:", client.get_state())
        print("Motor states:", client.get_motor_states())
        print("Beam position:", client.get_beam_position())
