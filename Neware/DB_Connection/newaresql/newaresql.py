import typing
import pathlib
import pandas as pd
import multiprocessing
import tqdm.auto as tqdm

from .src import sql
from .src import writers
from .src import transform


def download_worker(arg):
    test, kwargs = arg
    test.download(**kwargs)
    return


class Test:
    def __init__(self, test, file_format, file_path, file_name, connection_string):
        """_summary_

        :param test: _description_
        :type test: _type_
        :param file_format:
        :type file_format: _type_
        :param file_path: _description_
        :type file_path: _type_
        :param file_name: file name format: <dev_uid>_<unit_id>_<channel_id>_<test_id>_<test_start_date>
        :type file_name: _type_
        :param connection_string: _description_
        :type connection_string: _type_
        """
        self.test = test
        self.connection_string = connection_string

        if file_path is None:
            pathlib.Path(__file__).resolve().parent.joinpath('data')

        if callable(file_path):
            file_path = file_path(self.test)

        if file_name is None:
            start_date = self.test.start_time.date(
            ).isoformat().replace('-', '_')
            file_name = f"{test.dev_uid:.0f}_{test.unit_id:.0f}_{test.chl_id:.0f}_{test.test_id:.0f}_{start_date}"

        if callable(file_name):
            file_name = file_name(self.test)

        self.writer = writers.get_writer(file_format)(file_path, file_name)
        return

    def download(self, update=True, n_rows=None):
        # Basic checks
        if not self.writer.exists:
            update = False

        # TODO: alternative is checking the `dataupdate` column if it has a newer datetime than now()
        # TODO: alternative check only `active` tests
        if (update) & (self.writer.exists):
            max_seq_id = self.get_max_seq_id()
        else:
            max_seq_id = 0
        try:
            data = transform.data(
                sql.download_test(self.connection_string, self.test, from_seq_id=max_seq_id, to_seq_id=n_rows))
            if update:
                self.writer.append(data)

            else:
                self.writer.write(data)
        except Exception as e:
            print(f'Error fetching,transforming or writing data {e}')
        return

    def get_max_seq_id(self):
        if self.writer.exists:
            max_seq_id = self.writer.read(columns='seq_id').max().seq_id
        else:
            max_seq_id = 0
        return max_seq_id


class NewareDB:
    def __init__(self,
                 connection_string: str,
                 file_format: typing.Union[str, callable] = 'parquet',
                 file_path: typing.Union[str, callable, None] = None,
                 file_name: typing.Union[callable, None] = None,
                 download: typing.Union[callable, None] = None
                 ):

        self.connection_string = connection_string
        self.file_format = file_format

        if file_path is None:
            file_path = pathlib.Path(
                __file__).resolve().parent.joinpath('data')

        self.table = sql.get_table(self.connection_string)
        self.tests = [Test(test, file_format, file_path, file_name,
                           connection_string) for _, test in self.table.iterrows()]

        if download is None:
            download = lambda *args: True
        self.check_download = download
        return

    def download(self,
                 update: bool = True,
                 n_rows: typing.Union[None, int] = None,
                 parallel: typing.Union[bool, int] = False
                 ):
        download_list = [
            test for test in self.tests if self.check_download(test.test)]
        download_worker_args = [
            (test, {'update': update, 'n_rows': n_rows}) for test in download_list]

        if parallel is False:
            for arg in tqdm.tqdm(download_worker_args, desc='Downloading data'):
                download_worker(arg)

        else:
            if isinstance(parallel, int):
                n_jobs = parallel
            else:
                n_jobs = multiprocessing.cpu_count()

            with multiprocessing.Pool(n_jobs) as pool:
                bar = pool.imap_unordered(
                    func=download_worker, iterable=download_worker_args)
                for _ in tqdm.tqdm(bar, desc='Downloading data', total=len(download_list)):
                    continue
        return
