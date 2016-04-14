from utils.DownloadManager import download_manager
from twisted.internet import reactor

def file_added(torrent_file):
    print(torrent_file.torrent_id)

def onConnect(result):

    magnet_uri = 'magnet:?xt=urn:btih:EAE94773C601303A2E9BB9E7C062DA93EF140C44&dn=%5bTUZI%5d%5bGochuumon%20wa%20Usagi%20Desuka2%5d%5b01%5d%5bGB%5d%5b1280X720%5d&tr=http%3a%2f%2f192.168.1.3%3a8000%2fannounce'

    d = download_manager.download(magnet_uri, '/home/konomi/Desktop')
    d.addCallback(file_added)
    d2 = download_manager.download('magnet:?xt=urn:btih:BBAEA0B31D99825AD5B5F358F711B0307633D8B8&dn=uTorrent.dmg&tr=http%3a%2f%2f192.168.1.3%3a8000%2fannounce', '/home/konomi/Documents')
    d2.addCallback(file_added)


download_manager.connect().addCallbacks(onConnect)


reactor.run()