"""Dependency-free Linux joystick input for Isaac Gym playback."""

from __future__ import annotations

import errno
import os
import struct
from typing import Dict, Tuple

import numpy as np


_EVENT = struct.Struct("IhBB")
_BUTTON = 0x01
_AXIS = 0x02
_INIT = 0x80


class XboxJoystick:
    """Read the kernel ``/dev/input/js*`` API without pygame or evdev.

    Defaults follow the Linux Xbox mapping: axes 0/1 are the left stick,
    axis 3 is right-stick X, button 5 is RB, and button 6 is Back.
    """

    def __init__(
        self,
        device: str = "/dev/input/js0",
        *,
        max_forward: float = 0.6,
        max_lateral: float = 0.0,
        max_yaw: float = 1.0,
        deadzone: float = 0.08,
        require_deadman: bool = True,
        left_x_axis: int = 0,
        left_y_axis: int = 1,
        right_x_axis: int = 3,
        deadman_button: int = 5,
        quit_button: int = 6,
    ):
        if not 0.0 <= deadzone < 1.0:
            raise ValueError("deadzone must be in [0, 1)")
        for name, value in (
            ("max_forward", max_forward),
            ("max_lateral", max_lateral),
            ("max_yaw", max_yaw),
        ):
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        try:
            self._fd = os.open(device, os.O_RDONLY | os.O_NONBLOCK)
        except OSError as exc:
            raise RuntimeError(
                f"Cannot open Xbox joystick {device}: {exc}. "
                "Check the path and read permission."
            ) from exc
        self.device = device
        self.max_forward = float(max_forward)
        self.max_lateral = float(max_lateral)
        self.max_yaw = float(max_yaw)
        self.deadzone = float(deadzone)
        self.require_deadman = bool(require_deadman)
        self.left_x_axis = left_x_axis
        self.left_y_axis = left_y_axis
        self.right_x_axis = right_x_axis
        self.deadman_button = deadman_button
        self.quit_button = quit_button
        self.axes: Dict[int, float] = {}
        self.buttons: Dict[int, bool] = {}
        self._closed = False
        print(
            f"Xbox: {device}; hold RB to drive, release for zero command; "
            "Back exits. Left stick=xy, right stick x=yaw."
        )

    @staticmethod
    def decode_event(payload: bytes) -> Tuple[int, int, int]:
        if len(payload) != _EVENT.size:
            raise ValueError(f"joystick event must be {_EVENT.size} bytes")
        _, value, event_type, number = _EVENT.unpack(payload)
        return value, event_type & ~_INIT, number

    def _consume(self, payload: bytes) -> None:
        value, event_type, number = self.decode_event(payload)
        if event_type == _AXIS:
            self.axes[number] = float(np.clip(value / 32767.0, -1.0, 1.0))
        elif event_type == _BUTTON:
            self.buttons[number] = bool(value)

    def _axis(self, number: int) -> float:
        value = self.axes.get(number, 0.0)
        return 0.0 if abs(value) <= self.deadzone else value

    def poll(self) -> Tuple[np.ndarray, bool]:
        while self._fd is not None:
            try:
                payload = os.read(self._fd, _EVENT.size)
            except BlockingIOError:
                break
            except OSError as exc:
                if exc.errno in (errno.ENODEV, errno.EIO):
                    raise RuntimeError(f"Xbox joystick disconnected: {self.device}") from exc
                raise
            if not payload:
                raise RuntimeError(f"Xbox joystick disconnected: {self.device}")
            self._consume(payload)

        should_quit = self.buttons.get(self.quit_button, False)
        enabled = not self.require_deadman or self.buttons.get(self.deadman_button, False)
        if not enabled:
            return np.zeros(3, dtype=np.float32), should_quit

        # Linux reports stick-up as negative. Positive policy y/yaw are left/CCW.
        command = np.asarray(
            [
                -self._axis(self.left_y_axis) * self.max_forward,
                -self._axis(self.left_x_axis) * self.max_lateral,
                -self._axis(self.right_x_axis) * self.max_yaw,
            ],
            dtype=np.float32,
        )
        return command, should_quit

    def close(self) -> None:
        if not self._closed and self._fd is not None:
            os.close(self._fd)
            self._closed = True


__all__ = ["XboxJoystick"]
