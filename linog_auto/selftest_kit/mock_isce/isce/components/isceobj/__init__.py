"""MOCK isceobj (linog_auto self-test only): createImage(), whose load(xml) gives width and length, all that the kit's
linog_save_insar_images.py asks of it (self-test T122)."""
import re


class _Image(object):
    width = length = None

    def load(self, xml):
        x = open(xml).read()
        self.width, self.length = (int(re.search(r'name="%s">\s*<value>(\d+)' % n, x).group(1)) for n in ('width', 'length'))


def createImage():
    return _Image()
