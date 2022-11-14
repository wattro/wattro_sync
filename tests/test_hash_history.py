import copy
import random
import unittest
import unittest.mock

from wattro_sync.hash_history import history
from wattro_sync.hash_history.history import HashHistory


class FileAccessMock(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_read_write = unittest.mock.patch(
            "wattro_sync.hash_history.history.read_write"
        ).start()
        self.mock_read_write.get_or_create.return_value = ("mock_path", False)
        self.mock_read_write.read.return_value = {}

    def tearDown(self) -> None:
        unittest.mock.patch.stopall()

    @staticmethod
    def gen_mock_hist(prefix: str = "a", entries: int = -1) -> HashHistory:
        if entries < 0:
            entries = random.randint(1, 10)
        return HashHistory(
            {f"{prefix}{i}": i.to_bytes(1, byteorder="big") for i in range(entries)}
        )

    @staticmethod
    def gen_list_of_dicts(
        keys: list[str] | None = None, entries: int = -1
    ) -> list[dict]:
        if keys is None:
            keys = [f"k{i}" for i in range(random.randint(1, 3))]
        if entries < 0:
            entries = random.randint(1, 10)
        result = []
        for i in range(entries):
            mapping = {key: random.choice([f"value{i}", i]) for key in keys}
            result.append(mapping)
        return result

    @staticmethod
    def get_ident(list_of_dict: list[dict]) -> str:
        return random.choice(list(list_of_dict[0].keys()))

    def gen_list_and_ident(self) -> tuple[list[dict], str]:
        list_of_dicts = self.gen_list_of_dicts()
        ident = self.get_ident(list_of_dicts)
        assert isinstance(ident, str)
        return list_of_dicts, ident


class TestHash(FileAccessMock):
    def test_get_empty(self) -> None:
        self.assertEqual({}, history._generate_from_values([], "key"))

    def test_get_history(self) -> None:
        list_of_dicts, ident = self.gen_list_and_ident()

        hist = history._generate_from_values(list_of_dicts, ident)

        self.assertEqual(len(hist), len(list_of_dicts))
        ident_list = [str(val[ident]) for val in list_of_dicts]
        for ident in hist.keys():
            self.assertIn(ident, ident_list)

    def test_time_stable_history(self) -> None:
        list_of_dicts, ident = self.gen_list_and_ident()

        hist1 = history._generate_from_values(list_of_dicts, ident)
        self.assertEqual(len(hist1), len(list_of_dicts))  # instead of 'sleep'
        hist2 = history._generate_from_values(list_of_dicts, ident)

        self.assertEqual(hist1, hist2)

    def test_list_sort_stable(self) -> None:
        list_of_dicts, ident = self.gen_list_and_ident()

        hist1 = history._generate_from_values(list_of_dicts, ident)
        random.shuffle(list_of_dicts)
        hist2 = history._generate_from_values(list_of_dicts, ident)

        self.assertEqual(hist1, hist2)

    def test_dict_sort_stable(self) -> None:
        list_of_dicts, ident = self.gen_list_and_ident()

        hist1 = history._generate_from_values(list_of_dicts, ident)
        shuffled_dicts = []
        for dict_ in list_of_dicts:
            keys = list(dict_.keys())
            random.shuffle(keys)
            shuffled_dicts.append({k: dict_[k] for k in keys})
        hist2 = history._generate_from_values(shuffled_dicts, ident)

        self.assertEqual(hist1, hist2)


class TestHistoryHandler(FileAccessMock):
    def setUp(self) -> None:
        super().setUp()
        self.mock_read_write.read.return_value = {"asset": self.gen_mock_hist()}

    def test_reads_on_create(self) -> None:
        history.HistoryHandler()
        self.mock_read_write.read.assert_called_once()

    def test_flush(self) -> None:
        old_file = self.mock_read_write.read()
        hh = history.HistoryHandler()
        hh.save()
        self.mock_read_write.write.assert_called_once_with("history", old_file)

    def test_udpate(self) -> None:
        old_file = copy.deepcopy(self.mock_read_write.read())
        hh = history.HistoryHandler()
        val_list, ident = self.gen_list_and_ident()
        val = val_list[0]
        target = list(old_file.keys())[0]
        hh.update(target, val, ident)
        hh.save()
        self.mock_read_write.write.assert_called_once()
        _, write_value = self.mock_read_write.write.mock_calls[0].args
        self.assertNotEqual(old_file, write_value)
        ident_val = str(val[ident])
        self.assertEqual(write_value[target][ident_val], history._hashed(val))


class TestIterChanged(FileAccessMock):
    def gen_list_ident_and_selfhist(self) -> tuple[list[dict], str, HashHistory]:
        to_check, ident = self.gen_list_and_ident()
        hist = history._generate_from_values(to_check, ident)
        return to_check, ident, hist

    def get_handler_with_hist(
        self, hist_file: dict, target: str = "target"
    ) -> history.HistoryHandler:
        self.mock_read_write.read.return_value = {target: hist_file}
        return history.HistoryHandler()

    def assertOneChanged(
        self,
        ident: str,
        ident_val: str,
        to_check: list[dict],
        handler: history.HistoryHandler,
        target: str = "target",
    ) -> None:
        try:
            expected = next(filter(lambda val: str(val[ident]) == ident_val, to_check))
        except StopIteration:
            self.fail(
                f"Mock setup error. Value with {ident_val = } for {ident = } in \n"
                f"{to_check = }\n"
            )
        changed_generator = handler.iter_changed(target, to_check, ident)
        try:
            next_dict = next(changed_generator)
        except StopIteration:
            self.fail(
                f"Unexpectetly no changes found for {target = }\n"
                f"{ident = }\n"
                f"{to_check = }\n"
                f"{handler.full_hist = }\n"
            )
        else:
            self.assertEqual(expected, next_dict)
        with self.assertRaises(StopIteration):
            next(changed_generator)

    def test_get_changed_no_init_data(self) -> None:
        hh = self.get_handler_with_hist({})
        to_check, ident = self.gen_list_and_ident()
        self.assertEqual(to_check, list(hh.iter_changed("target", to_check, ident)))

    def test_get_nothing_on_same(self) -> None:
        to_check, ident, hist = self.gen_list_ident_and_selfhist()
        hh = self.get_handler_with_hist(hist)
        self.assertEqual([], list(hh.iter_changed("target", to_check, ident)))

    def test_get_changed_correct_target(self) -> None:
        to_check, ident, hist = self.gen_list_ident_and_selfhist()
        hh = self.get_handler_with_hist(hist)
        self.assertEqual(
            to_check, list(hh.iter_changed("other target", to_check, ident))
        )

    def test_finds_missing(self) -> None:
        to_check, ident, hist = self.gen_list_ident_and_selfhist()

        ident_val = random.choice(list(hist.keys()))
        hist.pop(ident_val)
        hh = self.get_handler_with_hist(hist)

        self.assertOneChanged(ident, ident_val, to_check, hh)

    def test_finds_changed(self) -> None:
        to_check, ident, hist = self.gen_list_ident_and_selfhist()

        ident_val = random.choice(list(hist.keys()))
        hist[ident_val] += "xxx"
        hh = self.get_handler_with_hist(hist)

        self.assertOneChanged(ident, ident_val, to_check, hh)


if __name__ == "__main__":
    unittest.main()
