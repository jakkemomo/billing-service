from unittest import mock

from aiohttp import StreamReader


def mock_stream(data):
    """Mock a stream with data."""
    protocol = mock.Mock(_reading_paused=False)
    stream = StreamReader(protocol, limit=2 ** 16)
    stream.feed_data(data)
    stream.feed_eof()
    return stream
