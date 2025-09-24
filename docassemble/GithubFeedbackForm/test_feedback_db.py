# do not pre-load

from testcontainers.postgres import PostgresContainer
from unittest import TestCase
from unittest.mock import patch


class TestFeedbackOnServer(TestCase):
    @classmethod
    def setUpClass(cls):
        cls._postgres = PostgresContainer("postgres:16")
        cls._postgres.start()
        cls._psql_url = cls._postgres.get_connection_url()

    @classmethod
    def tearDownClass(cls):
        cls._postgres.stop()

    @patch("docassemble.base.sql.alchemy_url")
    def test_minimal_db(self, url1):
        url1.return_value = self.__class__._psql_url
        from .feedback_on_server import save_good_or_bad, get_good_or_bad

        save_good_or_bad(1, interview="unittest", version="1.0.0")
        save_good_or_bad(-1, interview="unittest", version="1.0.0")

        save_good_or_bad(1, interview="unittest", version="1.0.1")
        save_good_or_bad(1, interview="unittest", version="1.0.1")
        save_good_or_bad(1, interview="unittest", version="1.0.1")

        ratings = get_good_or_bad("unittest")
        self.assertEqual(len(ratings), 2)
        self.assertListEqual([r["interview"] for r in ratings], ["unittest"] * 2)
        self.assertEqual(ratings[0]["average"], 1)
        self.assertEqual(ratings[1]["average"], 0)
