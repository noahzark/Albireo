from utils.DownloadManager import download_manager
from twisted.internet import reactor

def file_added(torrent_file):
    print(torrent_file.torrent_id)

def onConnect(result):

    magnet_uri = 'magnet:?xt=urn:btih:00163C7C108B2055ED1D51C2B150FBDE5C5F6A84&dn=%5bSumiSora%5d%5baokana%5d%5b12%5d%5bGB%5d%5b720p%5d.mp4&tr=http%3a%2f%2f192.168.1.3%3a8000%2fannounce'

    d = download_manager.download(magnet_uri, '/home/konomi/Desktop')
    d.addCallback(file_added)
    d2 = download_manager.download('magnet:?xt=urn:btih:BBAEA0B31D99825AD5B5F358F711B0307633D8B8&dn=uTorrent.dmg&tr=http%3a%2f%2f192.168.1.3%3a8000%2fannounce', '/home/konomi/Documents')
    d2.addCallback(file_added)


download_manager.connect().addCallbacks(onConnect)


reactor.run()