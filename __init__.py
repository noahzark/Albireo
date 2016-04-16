from utils.DownloadManager import download_manager
from twisted.internet import reactor

def file_added(torrent_file):
    print(torrent_file.torrent_id)

def onConnect(result):

    magnet_uri = 'magnet:?xt=urn:btih:0266EF22993330E9090A74A94E908DCF96594819&dn=%5bKTXP%5d%5bWakaba%20Girl%5d%5b01%5d%5bGB%5d.mp4&tr=http%3a%2f%2f192.168.1.3%3a8000%2fannounce'

    d = download_manager.download(magnet_uri, '/home/konomi/Desktop')
    d.addCallback(file_added)


download_manager.connect().addCallbacks(onConnect)


reactor.run()