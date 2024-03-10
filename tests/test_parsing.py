import unittest
from itertools import permutations

from parameterized import parameterized

from neurons.parsing import parse, INVALID
import pytz
from datetime import datetime

WEBSERVER_LOGLINE_FIELDS = ['ip',
                            'timestamp',
                            'method',
                            'url',
                            'protocol',
                            'status_code',
                            'bytes_sent'
                            ]
REQUEST_FIELDS = ['method', 'url', 'protocol']


class LogLineParserTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        now = datetime.now(pytz.timezone('UTC'))
        now_without_ms = now.replace(microsecond=0)
        cls.now_without_ms = now_without_ms
        cls.timestamp_str = f'[{now_without_ms.strftime("%d/%b/%Y %H:%M:%S %z")}]'

    @parameterized.expand([
        ("192.168.1.1", "GET", "200", 5432),
        ("192.168.1.2", "POST", "510", 0),
        ("192.1.1.1", "PUT", "201", 1),
        ("127.0.0.1", "DELETE", "500", 115151515),
    ])
    def test_parse_standard_order(self, ip, method, status_code, bytes_sent):
        data_dict = {
            'ip': ip,
            'timestamp': self.now_without_ms,
            'request_info': f'"{method} /index.html HTTP/1.1"',
            'status_code': status_code,
            'bytes_sent': bytes_sent,
        }
        logline = (f"{data_dict['ip']} - - {self.timestamp_str} {data_dict['request_info']} {data_dict['status_code']} "
                   f"{data_dict['bytes_sent']}")
        # should look like: '192.168.1.1 - - [09/Mar/2024 13:55:36 +0000] "GET /index.html HTTP/1.1" 200 5432'

        parsed_dict = parse(logline)

        # check the presence of all keys
        assert [key in parsed_dict for key in WEBSERVER_LOGLINE_FIELDS]

        # check the value of each key
        for key in WEBSERVER_LOGLINE_FIELDS:
            if key in REQUEST_FIELDS:
                assert parsed_dict[key] in data_dict["request_info"]
            else:
                assert parsed_dict[key] == data_dict[key]

    @parameterized.expand([(list(perm),) for perm in permutations([0, 1, 2, 3, 4])])
    def test_parse_different_order(self, order):
        """We test that a logline with the same data but in different order is parsed with the same result
        In the variable order we parametrize all the possible orders of a list of 5 elements"""
        data_dict = {
            'ip': "192.168.1.1",
            'timestamp': self.now_without_ms,
            'request_info': '"GET /index.html HTTP/1.1"',
            'status_code': "200",
            'bytes_sent': 5432,
        }
        timestamp_str = f'[{self.now_without_ms.strftime("%d/%b/%Y %H:%M:%S %z")}]'

        list_of_data = [
            data_dict['ip'],
            self.timestamp_str,
            data_dict['request_info'],
            data_dict['status_code'],
            data_dict['bytes_sent']
        ]
        # We reorder the list_of_data according to the order variable
        reordered_data = [list_of_data[i] for i in order]

        logline = (f"{reordered_data[0]} "
                   f"{reordered_data[1]} "
                   f"{reordered_data[2]} "
                   f"{reordered_data[3]} "
                   f"{reordered_data[4]}")

        parsed_dict = parse(logline)

        # check the value of each key
        for key in WEBSERVER_LOGLINE_FIELDS:
            if key in REQUEST_FIELDS:
                assert parsed_dict[key] in data_dict["request_info"]
            else:
                assert parsed_dict[key] == data_dict[key]

    def test_parse_empty(self):
        parsed_dict = parse('')
        assert parsed_dict
        for key in WEBSERVER_LOGLINE_FIELDS:
            assert parsed_dict[key] == INVALID
