import tempfile
import unittest
from pathlib import Path
from skilldemo.experiment import exclusive_run


class ExperimentLockTests(unittest.TestCase):
    def test_experiment_uses_server_directory_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            with exclusive_run(directory):
                self.assertTrue((Path(directory)/'server.lock').exists())
                with self.assertRaises((OSError,RuntimeError)):
                    with exclusive_run(directory):self.fail('Concurrent owner entered')
            with exclusive_run(directory):pass


if __name__=='__main__':unittest.main()
