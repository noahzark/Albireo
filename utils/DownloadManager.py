from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet import threads
from download_adapter.DelugeDownloader import DelugeDownloader
from domain.TorrentFile import TorrentFile
from domain.Episode import Episode
from domain.Bangumi import Bangumi
from utils.SessionManager import SessionManager
from utils.VideoManager import video_manager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DownloadManager:

    def __init__(self, downloader_cls):
        self.downloader = downloader_cls(self.on_download_completed)

    def connect(self):
        '''
        connect to a downloader daemon, currently use deluge.
        :return: a Deferred object
        '''
        return self.downloader.connect_to_daemon()


    def on_download_completed(self, torrent_id):
        logger.info('Download complete: %s', torrent_id)

        def create_thumbnail(episode, file_path):
            time = '00:02:00.000'
            video_manager.create_episode_thumbnail(episode, file_path, time)

        def update_torrent_file(file_path):
            session = SessionManager.Session
            torrent_file = session.query(TorrentFile).filter(TorrentFile.torrent_id == torrent_id).one()
            torrent_file.file_path = file_path

            # update status of episode
            episode = session.query(Episode).filter(Episode.torrent_files.contains(torrent_file)).one()
            episode.update_time = datetime.now()
            episode.status = Episode.STATUS_DOWNLOADED

            #update bangumi update_time

            bangumi = session.query(Bangumi).filter(Bangumi.episodes.contains(episode)).one()
            bangumi.update_time = datetime.now()

            session.commit()

            create_thumbnail(episode, file_path)


        def get_files(files):
                print files
                file_path = None
                if len(files) == 1:
                    # only one file
                    file_path = files[0]['path']
                elif len(files) > 1:
                    max_size = files[0]['size']
                    main_file = files[0]
                    for file in files:
                        if file['size'] > max_size:
                            main_file = file

                    file_path = main_file['path']
                else:
                    logger.warn('no file found in %s', torrent_id)

                if file_path is not None:
                    threads.deferToThread(update_torrent_file, file_path)

        def fail_to_get_files(result):
            logger.warn('fail to get files of %s', torrent_id)
            logger.warn(result)

        d = self.downloader.get_files(torrent_id)
        d.addCallback(get_files)
        d.addErrback(fail_to_get_files)

    @inlineCallbacks
    def download(self, magnet_uri, download_location):
        try:
            torrent_id = yield self.downloader.download(magnet_uri, download_location)
            returnValue(TorrentFile(torrent_id=torrent_id))
        except Exception as error:
            logger.warn(error)
            returnValue(None)


download_manager = DownloadManager(DelugeDownloader)
