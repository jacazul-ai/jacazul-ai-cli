import os
import unittest
import json
from jacazul.taskwarrior.core import (
    BrokerFactory,
    GitHubBroker,
    BitbucketBroker,
)


class TestBrokerOverride(unittest.TestCase):
    def setUp(self):
        self.config_path = os.path.expanduser("~/.jacazul-ai/brokers.json")
        if os.path.exists(self.config_path):
            os.rename(self.config_path, self.config_path + ".bak")

    def tearDown(self):
        if os.path.exists(self.config_path + ".bak"):
            os.rename(self.config_path + ".bak", self.config_path)
        elif os.path.exists(self.config_path):
            os.remove(self.config_path)

    def test_default_patterns(self):
        # Padrões atuais (GitHub e Bitbucket fixo)
        self.assertIsInstance(BrokerFactory.get_broker("#123"), GitHubBroker)
        self.assertIsInstance(
            BrokerFactory.get_broker("PROJ-123"), BitbucketBroker
        )

    def test_config_override_pattern(self):
        # Config override for a pattern not accepted today
        # (lowercase + colon)
        config = {
            "patterns": [{"regex": r"^jira:[0-9]+$", "broker": "bitbucket"}]
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(config, f)

        # Should fail now (return None) — override not yet in code
        broker = BrokerFactory.get_broker("jira:123")
        print(f"DEBUG: Broker for jira:123 is {type(broker)}")
        self.assertIsInstance(
            broker,
            BitbucketBroker,
            "Should match BitbucketBroker via custom regex 'jira:123'",
        )


if __name__ == "__main__":
    unittest.main()
