import logging
import json
import os
import sys
import time
from datetime import datetime

import utils

import crcmod._crcfunext
import oss2

logger = logging.getLogger(__name__)

configs = {
    'BackupDir': 'data',
    'AccessKey': 'LTAIYDoYZXgvVe8t',
    'AccessSecret': 'VvNx7s7EGWduHZ1Oj91VFtP8Cvbv5H',
    'BucketName': 'photo-bak',
    'Endpoint': 'https://oss-cn-beijing.aliyuncs.com'
}


class OssSychronizer(object):
    def __init__(self, access_key, access_secret, bucket_name, endpoint, bakdir):
        self.auth = oss2.Auth(access_key, access_secret)
        self.bucket = oss2.Bucket(self.auth, endpoint, bucket_name)
        self.backup_dir = bakdir
        self.interval = 30  # 30 second
        self.exec_dir = os.getcwd()

    def __sync_file(self, dirname, ct):
        utils.mkdir(dirname)
        try:
            os.chdir(dirname)
        except:
            logger.error('No such directory: {0}'.format(dirname))
            return

        for obj in oss2.ObjectIterator(self.bucket):
            if obj.key[-1] == '/':
                utils.mkdir(obj.key)
                continue
            else:
                if ct < obj.last_modified:
                    #timestr = datetime.utcfromtimestamp(obj.last_modified).strftime('%Y-%M-%d %H:%M:%S')
                    if os.path.exists(obj.key):
                        logger.info('File already downloaded: ' + obj.key)
                        continue
                    # Start to download file
                    try:
                        self.bucket.get_object_to_file(obj.key, obj.key, progress_callback=utils.percentage)
                        logger.info('Download file successfully: ' + obj.key)
                    except oss2.exceptions.NoSuchKey:
                        logger.warn('No such object key: {0}'.format(obj.key))
                    except:
                        logger.error('Unexpected error: ' + sys.exc_info()[0])
                        exit(1)

        os.chdir(self.exec_dir)

    def sync_file_first(self):
        self.__sync_file(self.backup_dir, 0)

    def sync_file_loop(self):
        current_time = int(time.time())
        while True:
            tmp = current_time
            self.__sync_file(self.backup_dir, tmp)
            current_time = int(time.time())
            time.sleep(self.interval)

    def sync(self):
        self.sync_file_first()
        self.sync_file_loop()


def main(argv):
    utils.parse_argv(argv)

    ossSync = OssSychronizer(configs['AccessKey'],
                             configs['AccessSecret'],
                             configs['BucketName'],
                             configs['Endpoint'],
                             configs['BackupDir'])
    ossSync.sync()


if __name__ == "__main__":
    main(sys.argv[1:])
