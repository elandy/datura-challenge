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


import time
from typing import List

# Bittensor
import bittensor as bt
import torch

from neurons.parsing import ParsedWebserverLogLine, INVALID
from neurons.protocol import WebServerLogLine

# import base validator class which takes care of most of the boilerplate
from template.base.validator import BaseValidatorNeuron
from template.utils.uids import get_random_uids
from template.validator.reward import get_rewards, reward

example_loglines = [
    '192.168.1.1 - - [09/Mar/2024 13:55:36 +0000] "GET /index.html HTTP/1.1" 200 5432',
    '[19/Mar/2023 13:55:36 +0000] 192.168.1.2 - - 200 "POST /index.html HTTP/1.2" 1234',
    '[21/Mar/2025 13:55:36 +0000] 192.168.1.3 - - 200 "PUT /index.html HTTP/1.1"'
    '192.168.1.4 - - 500 "GET /index.html HTTP/1.1"'
    '192.168.1.5 - - 200'
    '',
]


class Validator(BaseValidatorNeuron):
    """
    Your validator neuron class. You should use this class to define your validator's behavior. In particular, you should replace the forward function with your own logic.

    This class inherits from the BaseValidatorNeuron class, which in turn inherits from BaseNeuron. The BaseNeuron class takes care of routine tasks such as setting up wallet, subtensor, metagraph, logging directory, parsing config, etc. You can override any of the methods in BaseNeuron if you need to customize the behavior.

    This class provides reasonable default behavior for a validator such as keeping a moving average of the scores of the miners and using them to set weights at the end of each epoch. Additionally, the scores are reset for new hotkeys at the end of each epoch.
    """

    def __init__(self, config=None):
        super(Validator, self).__init__(config=config)

        bt.logging.info("load_state()")
        self.load_state()

    async def forward(self):
        """
        Validator forward pass. Consists of:
        - Generating the query
        - Querying the miners
        - Getting the responses
        - Rewarding the miners
        - Updating the scores

        The validator validates that the parsed logline returned by the miner has the correct format
        The reward is based on the amount of keys of the ParsedWebserverLogLine that the miner was able to fill
        This rewards miners with better parsing mechanisms that capture as much data from the logline as possible
        """
        miner_uids = get_random_uids(self, k=self.config.neuron.sample_size)

        logline_input = example_loglines[self.step % len(example_loglines)]
        bt.logging.info(f"Sent logline to parse: {logline_input}")

        # The dendrite client queries the network.
        responses = await self.dendrite(
            # Send the query to selected miner axons in the network.
            axons=[self.metagraph.axons[uid] for uid in miner_uids],
            # Construct a WebServerLogLine query. This contains a Web Server Log Line as a string.
            # For this exercise, the logline is taken in a roundrobin way from the example_loglines list
            synapse=WebServerLogLine(logline_input=logline_input),
            # All responses have the deserialize function called on them before returning.
            # You are encouraged to define your own deserialization function.
            deserialize=True,
        )

        # Log the results for monitoring purposes.
        bt.logging.info(f"Received responses: {responses}")

        # Adjust the scores based on responses from miners.
        rewards = self.get_rewards(self, query=logline_input, responses=responses)

        bt.logging.info(f"Scored responses: {rewards}")
        # Update the scores based on the rewards. You may want to define your own update_scores function for custom
        # behavior.
        self.update_scores(rewards, miner_uids)

    def get_rewards(
        self,
        query: str,
        responses: List[dict],
    ) -> torch.FloatTensor:
        """
        Returns a tensor of rewards for the given query and responses.

        Args:
        - query (str): The query sent to the miner.
        - responses (List[dict]): A list of responses from the miner.

        Returns:
        - torch.FloatTensor: A tensor of rewards for the given query and responses.
        """
        # Get all the reward results by iteratively calling your reward() function.
        return torch.FloatTensor(
            [reward(query, response) for response in responses]
        ).to(self.device)

    def reward(query: str, response: dict) -> float:
        """
        Reward the miner response to the dummy request. This method returns a reward
        value for the miner, which is used to update the miner's score.

        Returns:
        - float: The reward value for the miner.
        """
        total_valid_keys = ParsedWebserverLogLine.__annotations__.keys()
        valid_keys = 0
        for valid_key in total_valid_keys:
            # count the amount of keys in the dictionary that the parsing mechanism was able to fill
            if response.get(valid_key):
                valid_keys += 1 if response[valid_key] not in [INVALID, ''] else 0

        # return 1.0 if all keys filled, else the percentage of filled keys
        return valid_keys / len(total_valid_keys)

    def save_state(self):
        """Override base save_state to avoid warnings"""
        pass  # override to avoid warnings


# The main function parses the configuration and runs the validator.
if __name__ == "__main__":
    with Validator() as validator:
        while True:
            bt.logging.info("Validator running...", time.time())
            time.sleep(5)
