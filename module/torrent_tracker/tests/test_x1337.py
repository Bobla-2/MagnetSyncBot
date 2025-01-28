import unittest
from unittest.mock import MagicMock, patch
from module.torrent_tracker.x1337.x1337 import TorrentInfo

class TestTorrentInfo(unittest.TestCase):
    def setUp(self):
        # Замоканный объект _1337ParserPage
        self.mock_parser = MagicMock()
        self.mock_parser.get_magnet.return_value = "mocked_magnet_link"
        self.mock_parser.get_other_data.return_value = "mocked_other_data"

        # Замена _1337ParserPage в классе TorrentInfo
        patcher = patch('module.torrent_tracker.x1337.x1337._1337ParserPage', return_value=self.mock_parser)
        self.addCleanup(patcher.stop)
        self.mock_parser_class = patcher.start()

        # Инициализация объекта TorrentInfo
        self.torrent_info = TorrentInfo(
            url="http://example.com/torrent",
            category="Movies",
            name="Example Movie",
            year="2025",
            magnet="magnet:?xt=urn:btih:examplehash",
            size="1.4 GB",
            seeds="200",
            leeches="50"
        )

    def test_name_property(self):
        expected_name = "Example Movie\n"
        self.assertEqual(self.torrent_info.name, expected_name)

    def test_get_magnet(self):
        self.assertEqual(self.torrent_info.get_magnet, "mocked_magnet_link")
        self.mock_parser.get_magnet.assert_called_once()

    def test_get_other_data(self):
        self.assertEqual(self.torrent_info.get_other_data, "mocked_other_data")
        self.mock_parser.get_other_data.assert_called_once()

    def test_id_torrent_property(self):
        self.assertIsNone(self.torrent_info.id_torrent)

        self.torrent_info.id_torrent = 123
        self.assertEqual(self.torrent_info.id_torrent, 123)

    def test_full_info_property(self):
        expected_info = (
            "Example Movie\n\n*Вес:* 1.4 GB\n*Категория:* Movies\n"
            "*leeches:* 50\n*seeds:* 200\n*дата:* 2025\nmocked_other_data\n"
            "[страница](http://example.com/torrent)"
        )
        self.assertEqual(self.torrent_info.full_info, expected_info)

    def test_slots(self):
        # Проверяем, что нельзя установить новый атрибут
        with self.assertRaises(AttributeError, msg="__slots__ не работает! Новый атрибут можно добавить"):
            self.torrent_info.new_attribute = "Should fail"


if __name__ == '__main__':
    unittest.main()
