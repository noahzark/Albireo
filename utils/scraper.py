# -*- coding: utf-8 -*-
from HTMLParser import HTMLParser
import cfscrape

class DMHYFileListScraper(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.level = 0
        self.file_path_list = []

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            for (name, value) in attrs:
                if name == 'id' and value == 'resource-tabs' and self.level == 0:
                    self.level = 1
                    break
                elif name == 'id' and value == 'tabs-1' and self.level == 1:
                    self.level = 2
                    break
                elif name == 'class' and value == 'file_list' and self.level == 2:
                    self.level = 3
                    break
        elif tag == 'li' and self.level == 3:
            self.level = 4

    def handle_endtag(self, tag):
        if tag == 'li' and self.level == 4:
            self.level = 3
        elif tag == 'div' and self.level == 3:
            self.level = 2
        elif tag == 'div' and self.level == 2:
            self.level = 1
        elif tag == 'div' and self.level == 1:
            self.level = 0

    def handle_data(self, data):
        if self.level == 4:
            striped_str = data.strip()
            if striped_str.endswith('.mp4'):
                self.file_path_list.append(striped_str)
