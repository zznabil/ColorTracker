
from unittest.mock import MagicMock

from utils.keyboard_listener import KeyboardListener


class MockKey:
    def __init__(self, char=None, name=None):
        self.char = char
        self.name = name

    def __str__(self):
        return self.char if self.char else self.name

def test_listen_for_single_key():
    config = MagicMock()
    listener = KeyboardListener(config)

    # Mock callback
    callback = MagicMock()

    # Start listening
    listener.listen_for_single_key(callback)

    assert listener._bind_mode is True
    assert listener._bind_callback == callback

    # Simulate key press
    key = MockKey(char='k')
    listener._on_key_press(key)

    # Verify callback called
    callback.assert_called_once_with('k')

    # Verify mode reset
    assert listener._bind_mode is False
    assert listener._bind_callback is None

def test_listen_for_single_key_special_key():
    config = MagicMock()
    listener = KeyboardListener(config)

    callback = MagicMock()
    listener.listen_for_single_key(callback)

    # Simulate special key press (e.g. F1)
    key = MockKey(name='f1')
    listener._on_key_press(key)

    callback.assert_called_once_with('f1')

def test_remove_callback():
    config = MagicMock()
    listener = KeyboardListener(config)

    callback = MagicMock()
    listener.register_callback('a', callback)

    assert 'a' in listener.callbacks
    assert 'press' in listener.callbacks['a']

    listener.remove_callback('a')

    assert 'a' not in listener.callbacks

def test_remove_callback_partial():
    config = MagicMock()
    listener = KeyboardListener(config)

    cb1 = MagicMock()
    cb2 = MagicMock()
    listener.register_callback('a', cb1, on_press=True)
    listener.register_callback('a', cb2, on_press=False)

    assert 'press' in listener.callbacks['a']
    assert 'release' in listener.callbacks['a']

    listener.remove_callback('a', on_press=True)

    assert 'press' not in listener.callbacks['a']
    assert 'release' in listener.callbacks['a']
    assert 'a' in listener.callbacks # Key still exists because release is there

    listener.remove_callback('a', on_press=False)
    assert 'a' not in listener.callbacks
