# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# Copyright © 2024 Andres Politi

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

from typing import Optional
import bittensor as bt

from neurons.parsing import ParsedWebserverLogLine


class WebServerLogLine(bt.Synapse):
    """
    A webserver logline protocol representation which uses bt.Synapse as its base.
    This protocol helps in handling logline parsing request and response communication between
    the miner and the validator.

    A webserver logline can have a format like this:
    '192.168.1.1 - - [09/Mar/2024 13:55:36 +0000] "GET /index.html HTTP/1.1" 200 5432'
    The order of the elements is not guaranteed, so any parsing efforts should be able to handle that.
    It could look like this (or any other order):
    '[09/Mar/2024 13:55:36 +0000] 192.168.1.1 - - 200 "GET /index.html HTTP/1.1" 5432'
    Notes:
        - method, url and protocol come always in the same order: "GET /index.html HTTP/1.1"
        - timestamp always comes between square brackets: [09/Mar/2024 13:55:36 +0000]

    Attributes:
    - logline_input: A string value representing the logline to be parsed
    - parsed_logline: An optional typedDict with fixed keynames for every possible element of the webserver logline
    """
    # Required request input, filled by sending dendrite caller.
    logline_input: str

    # Optional request output, filled by receiving axon.
    parsed_logline: Optional[ParsedWebserverLogLine] = None

    def deserialize(self) -> ParsedWebserverLogLine:
        """
        Deserialize the output. This method retrieves the response from
        the miner in the form of parsed_logline, deserializes it and returns it
        as the output of the dendrite.query() call.

        Returns:
        - ParsedWebserverLogLine: The deserialized response, which in this case is the value of parsed_logline.

        Example:
        Assuming an input logline instance has the following parsed output:
        >>> logline_instance = WebServerLogLine(logline_input)
        '192.168.1.1 - - [09/Mar/2024 13:55:36 +0000] "GET /index.html HTTP/1.1" 200 5432')
        >>> logline_instance.parsed_logline = parse(logline_input)
        >>> logline_instance.deserialize()
        {
            'ip': '192.168.1.1',
            'timestamp': datetime.datetime(2024, 3, 9, 13, 55, 36, tzinfo=tzutc()),
            'method': 'GET',
            'url': '/index.html',
            'protocol': 'HTTP/1.1',
            'status_code': 200,
            'bytes_sent': 5432
        }
        """
        return self.parsed_logline


