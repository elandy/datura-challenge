import ipaddress
import typing

from dateutil.parser import parse as parse_date
import datetime
import re
from typing import Optional


INVALID = "INVALID"  # Represents invalid data parsed from the logline, like malformed ips or urls
METHODS = ["GET", "POST", "PUT", "DELETE"]


class ParsedWebserverLogLine(typing.TypedDict):
    ip: Optional[str]
    timestamp: Optional[typing.Union[datetime.datetime, INVALID]]
    method: Optional[str]
    url: Optional[str]
    protocol: Optional[str]
    status_code: Optional[typing.Union[str, INVALID]]
    bytes_sent: Optional[typing.Union[int, INVALID]]


def parse(logline_input):
    patterns = {
        "ip": r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
        "timestamp": r'\[(?P<timestamp>.*?)\]',

        # method, url and protocol are captured with one regex because they always come in the same order
        "request_info": r'"(?P<method>.*) (?P<url>/\S+) (?P<protocol>HTTP/\d\.\d)"',

        # negative lookahead and lookbehind to ensure the 3 digits captured are not part of the ip address
        # or the bytes sent
        "status_code": r'(?<![\d.])\d{3}(?![\d.])',
        "bytes_sent": r'\d+'
    }

    # Initialize an empty dictionary to store extracted information
    extracted_info = {}
    # Initialize variable to store a copy of the logline, so it can be modified after running each regex
    remaining_logline = logline_input

    # Extract information using patterns
    for key, pattern in patterns.items():
        match = re.search(pattern, remaining_logline)
        if match:
            # remove already extracted info from remaining_logline
            remaining_logline = re.sub(pattern, '', remaining_logline, count=1)
            extracted_info[key] = match

    extracted_info = transform_extracted_info(extracted_info)

    return ParsedWebserverLogLine(**extracted_info)


def transform_extracted_info(extracted_info):
    try:
        ip = extracted_info.get('ip').group()
        ipaddress.ip_address(ip)
        extracted_info["ip"] = ip
    except (ValueError, AttributeError):  # invalid ip
        extracted_info['ip'] = INVALID

    try:
        timestamp_match = extracted_info.get("timestamp").group("timestamp")
        extracted_info["timestamp"] = parse_date(timestamp_match)
    except AttributeError:
        extracted_info["timestamp"] = INVALID

    request_match = extracted_info.get("request_info")
    if request_match:
        extracted_info["method"] = request_match.group('method')
        if extracted_info["method"] not in METHODS:
            extracted_info["method"] = INVALID
        extracted_info["url"] = request_match.group('url')
        extracted_info["protocol"] = request_match.group('protocol')
        del extracted_info["request_info"]
    else:
        extracted_info["method"] = INVALID
        extracted_info["url"] = INVALID
        extracted_info["protocol"] = INVALID

    status_code_match = extracted_info.get("status_code")
    if status_code_match:
        extracted_info["status_code"] = status_code_match.group()
    else:
        extracted_info["status_code"] = INVALID

    bytes_sent_match = extracted_info.get("bytes_sent")
    if bytes_sent_match:
        extracted_info["bytes_sent"] = int(bytes_sent_match.group())
    else:
        extracted_info["bytes_sent"] = INVALID

    return extracted_info
