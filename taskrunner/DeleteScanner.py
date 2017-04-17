import logging
import json
import shutil
import os
from twisted.internet.task import LoopingCall
from twisted.internet import threads, reactor
from twisted.internet.defer import inlineCallbacks
from datetime import datetime, timedelta

from utils.SessionManager import SessionManager
from utils.db import row2dict
from utils.DownloadManager import download_manager
from domain.Bangumi import Bangumi
from domain.Task import Task
from domain.Episode import Episode
from domain.WatchProgress import WatchProgress
from domain.Favorites import Favorites
from domain.VideoFile import VideoFile

logger = logging.getLogger(__name__)

class DeleteScanner:


    def __init__(self, base_path, delete_delay):
        self.interval = 120
        self.base_path = base_path
        self.bangumi_delete_delay = delete_delay['bangumi']
        self.episode_delete_delay = delete_delay['episode']

    def start(self):
        lc = LoopingCall(self.scan_delete)
        lc.start(self.interval)

    def __unshift_task_step(self, task_content, task, session):
        task_content['task_step'].pop(0)
        task.content = json.dumps(task_content)
        session.commit()

    def delete_bangumi(self, bangumi):
        session = SessionManager.Session()
        try:
            # add related information to database
            task_content = {'bangumi_id': str(bangumi.id)}
            episode_list = session.query(Episode).filter(Episode.bangumi_id == bangumi.id).all()
            episode_id_list = [episode.id for episode in episode_list]
            video_file_list = session.query(VideoFile).filter(VideoFile.bangumi_id == bangumi.id).all()
            watch_progress_list = session.query(WatchProgress).filter(WatchProgress.episode_id.in_(episode_id_list)).all()
            favorite_list = session.query(Favorites).filter(Favorites.bangumi_id == bangumi.id).all()

            task_content['torrent_id_list'] = list(set([video_file.torrent_id for video_file in video_file_list]))
            task_content['task_step'] = ['db', 'torrent', 'file_system']

            task = Task(type = Task.TYPE_BANGUMI_DELETE, content = json.dumps(task_content), status = Task.STATUS_IN_PROGRESS)
            session.add(task)
            session.commit()


            # video file
            for video_file in video_file_list:
                session.delete(video_file)

            # remove watch-progress
            for watch_progress in watch_progress_list:
                session.delete(watch_progress)

            # remove episode
            for episode in episode_list:
                session.delete(episode)

            # remove favorites
            for favorite in favorite_list:
                session.delete(favorite)

            # remove bangumi
            session.delete(bangumi)

            self.__unshift_task_step(task_content, task, session)

            if len(task_content['torrent_id_list']) > 0:
                # remove torrent from deluge
                try:
                    threads.blockingCallFromThread(reactor, download_manager.remove_torrents, task_content['torrent_id_list'], False)
                except Exception as error:
                    logger.warn(error)
            self.__unshift_task_step(task_content, task, session)

            # remove files of bangumi
            bangumi_folder_path = '{0}/{1}'.format(self.base_path, str(bangumi.id))
            shutil.rmtree(bangumi_folder_path, ignore_errors=True)
            task_content['task_step'].pop(0)
            task.content = json.dumps(task_content)
            task.status = Task.STATUS_COMPLETE
            session.commit()

            return str(task.id)
        finally:
            SessionManager.Session.remove()

    def delete_episode(self, episode):
        session = SessionManager.Session()
        try:
            task_content= {'episode_id': str(episode.id)}
            video_file_list = session.query(VideoFile).\
                filter(VideoFile.episode_id == episode.id).\
                all()

            watch_progress_list = session.query(WatchProgress).filter(
                WatchProgress.episode_id == episode.id).all()

            task_content['video_file_list'] = [row2dict(video_file) for video_file in video_file_list]

            task_content['task_step'] = ['db', 'torrent',  'file_system']

            task = Task(type = Task.TYPE_EPISODE_DELETE, content = json.dumps(task_content), status = Task.STATUS_IN_PROGRESS)
            session.add(task)
            session.commit()

            for video_file in video_file_list:
                session.delete(video_file)

            # remove watch-progress
            for watch_progress in watch_progress_list:
                session.delete(watch_progress)

            # remove episode
            session.delete(episode)

            self.__unshift_task_step(task_content, task, session)

            # remove torrent
            if len(task_content['video_file_list']) > 0:
                threads.blockingCallFromThread(reactor, download_manager.remove_torrents, task_content['video_file_list']['torrent_id'], True)

            self.__unshift_task_step(task_content, task, session)


            # remove files of episode
            bangumi_folder_path = '{0}/{1}'.format(self.base_path, str(episode.bangumi_id))
            for torrent_file in task_content['video_file_list']:
                file_path = '{0}/{1}'.format(bangumi_folder_path, torrent_file['file_path'])
                os.remove(file_path)

            task_content['task_step'].pop(0)
            task.content = json.dumps(task_content)
            task.status = Task.STATUS_COMPLETE

            session.commit()
            return str(task.id)

        finally:
            SessionManager.Session.remove()

    def __dispatch_delete_bangumi(self, bangumi_list):
        for bangumi in bangumi_list:
            d = threads.deferToThread(self.delete_bangumi, bangumi)
            d.addCallback(self.__on_delete_callback)
            d.addErrback(self.__on_delete_errCallback)

    def __dispatch_delete_episode(self, episode_list):
        for episode in episode_list:
            d = threads.deferToThread(self.delete_episode, episode)
            d.addCallback(self.__on_delete_callback)
            d.addErrback(self.__on_delete_errCallback)

    def __on_delete_callback(self, id):
        logger.debug('delete task id#{0} added'.format(id,))

    def __on_delete_errCallback(self, err):
        logger.warn(err)

    def __query_error(self, err):
        logger.warn(err)

    def scan_bangumi(self):
        session = SessionManager.Session()
        try:
            task_list = session.query(Task).\
                filter(Task.status != Task.STATUS_COMPLETE).\
                filter(Task.type == Task.TYPE_BANGUMI_DELETE).\
                all()
            bangumi_id_in_task = []
            for task in task_list:
                content_dict = json.loads(task.content)
                bangumi_id_in_task.append(content_dict['bangumi_id'])

            latest_delete_time = datetime.now() - timedelta(minutes=self.bangumi_delete_delay)

            query = session.query(Bangumi)

            if len(bangumi_id_in_task) > 0:
                query = query.filter(Bangumi.id.notin_(bangumi_id_in_task))

            bangumi_list = query.\
                filter(Bangumi.delete_mark != None).\
                filter(Bangumi.delete_mark <= latest_delete_time).\
                all()

            return bangumi_list
        finally:
            SessionManager.Session.remove()

    def scan_episode(self):
        session = SessionManager.Session()
        try:
            task_list = session.query(Task). \
                filter(Task.status != Task.STATUS_COMPLETE). \
                filter((Task.type == Task.TYPE_EPISODE_DELETE) | (Task.type == Task.TYPE_BANGUMI_DELETE)).\
                all()
            episode_id_in_task = []
            bangumi_id_in_task = []
            for task in task_list:
                content_dict = json.loads(task.content)
                if task.type == Task.TYPE_EPISODE_DELETE:
                    episode_id_in_task.append(content_dict['episode_id'])
                else:
                    bangumi_id_in_task.append(content_dict['bangumi_id'])

            latest_delete_time = datetime.now() - timedelta(minutes=self.episode_delete_delay)

            query = session.query(Episode)

            if len(episode_id_in_task) > 0:
                query = query.filter(Episode.id.notin_(episode_id_in_task))

            if len(bangumi_id_in_task) > 0:
                query = query.filter(Episode.bangumi_id.notin_(bangumi_id_in_task))

            episode_list = query.\
                filter(Episode.delete_mark != None).\
                filter(Episode.delete_mark <= latest_delete_time).\
                all()

            return episode_list
        finally:
            SessionManager.Session.remove()

    def scan_delete(self):
        logger.info('scan delete')
        bgm_d = threads.deferToThread(self.scan_bangumi)
        bgm_d.addCallback(self.__dispatch_delete_bangumi)
        bgm_d.addErrback(self.__query_error)

        eps_d = threads.deferToThread(self.scan_episode)
        eps_d.addCallback(self.__dispatch_delete_episode)
        eps_d.addErrback(self.__query_error)
