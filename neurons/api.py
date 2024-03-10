import bittensor as bt
from typing import List, Union, Any
from bittensor.subnets import SubnetsAPI

from neurons.protocol import WebServerLogLine


class WebServerLogLineAPI(SubnetsAPI):
    def __init__(self, wallet: "bt.wallet"):
        super().__init__(wallet)
        self.netuid = 33
        self.name = "dummy"

    def prepare_synapse(self, logline_input: str) -> WebServerLogLine:
        synapse.logline_input = logline_input
        return synapse

    def process_responses(
        self, responses: List[Union["bt.Synapse", Any]]
    ) -> List[dict]:
        outputs = []
        for response in responses:
            if response.dendrite.status_code != 200:
                continue
            return outputs.append(response.parsed_logline)
        return outputs
