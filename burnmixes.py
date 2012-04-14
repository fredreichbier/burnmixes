#!/usr/bin/env python2
import xml.etree.ElementTree as ET
import argparse
import logging
import os
from subprocess import Popen

import mad

PART_LENGTH = 3 * 60 * 1000 # 3 minutes
CD_LENGTH = 70 * 60 * 1000 # 70 minutes

logging.basicConfig(format='%(message)s', level=logging.DEBUG)

log = logging.getLogger(__name__)

class Part(object):
    def __init__(self, filename, start, end, artist, title):
        self.filename = filename
        self.start = start
        self.end = end
        self.artist = artist
        self.title = title

    @property
    def brasero_start(self):
        """ Return start in nanoseconds """
        return self.start * 1000 * 1000

    @property
    def brasero_end(self):
        """ Return end in nanoseconds """
        return self.end * 1000 * 1000

def get_file_length(filename):
    """
        Return the length (in milliseconds) of the mp3 file *filename*.
    """
    mf = mad.MadFile(filename)
    return mf.total_time()

def split_file(filename, artist, title_template, part_length=PART_LENGTH):
    """
        Yield `Part` instances.
    """
    length = get_file_length(filename)
    log.info('Total MP3 length in ms: %d' % length)
    start = 0
    idx = 1
    while length > part_length:
        # new part!
        yield Part(filename, start, start + part_length - 1, artist, title_template % idx)
        start += part_length
        length -= part_length
        idx += 1
    if length > 0:
        # last track!
        yield Part(filename, start, start + length, artist, title_template % idx)

def split_cds(parts, cd_length=CD_LENGTH):
    """
        Yield lists of Part instances (one for each CD).
    """
    cds = 1
    current_cd = []
    for part in parts:
        if part.end > cds * cd_length:
            # ow! new cd. yield old cd.
            log.info('Creating CD %d with %d parts ...' % (cds, len(current_cd)))
            yield current_cd
            cds += 1
            current_cd = []
        current_cd.append(part)
    if current_cd:
        log.info('Creating CD %d with %d parts ...' % (cds, len(current_cd)))
        yield current_cd

def build_project(parts, label):
    """
        Return an `ElementTree.ElementTree` instance (a brasero project).
    """
    root = ET.Element('braseroproject')
    version = ET.SubElement(root, 'version')
    version.text = '0.2'
    label_elem = ET.SubElement(root, 'label')
    label_elem.text = label
    track = ET.SubElement(root, 'track')
    for part in parts:
        audio = ET.SubElement(track, 'audio')
        uri = ET.SubElement(audio, 'uri')
        uri.text = 'file://%s' % part.filename
        start = ET.SubElement(audio, 'start')
        start.text = str(part.brasero_start)
        end = ET.SubElement(audio, 'end')
        end.text = str(part.brasero_end)
        title = ET.SubElement(audio, 'title')
        title.text = part.title
        artist = ET.SubElement(audio, 'artist')
        artist.text = part.artist
    return ET.ElementTree(root)

def build_projects(filename, artist, title_template, label_template, part_length=PART_LENGTH, cd_length=CD_LENGTH):
    """
        Build multiple projects and yield them (as ElementTree instances). Yay!
        *label_template* is a string with a `%d` placeholder for the cd index (starting at 1).
    """
    parts = split_file(filename, artist, title_template, part_length)
    cds = split_cds(parts, cd_length)
    for idx, cd in enumerate(cds, 1):
        yield build_project(cd, label_template % idx)

def burn_project(filename, invoke):
    """ Invoke brasero to burn the project. """
    commandline = (invoke % os.path.abspath(filename)).encode('string-escape')
    log.info('Burning, commandline: %s' % commandline)
    proc = Popen(commandline, shell=True)
    if proc.wait() != 0:
        log.error('Burning application didn\'t exit cleanly, exiting ...')
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Burn looooong MP3 files on CDs.')
    parser.add_argument('filename', metavar='FILENAME', help='The MP3 file to burn')
    parser.add_argument('-a', '--artist', required=True, dest='artist',
            help='Artist\'s name')
    parser.add_argument('-t', '--track', required=True, dest='track',
            help='The track name template containing %%d -- it will be replaced with the track ID')
    parser.add_argument('-l', '--label', default=None, dest='label',
            help='The label template containing %%d (the CD index). Can be automatically '
                 'constructed from the artist and track')
    parser.add_argument('-p', '--part-length', default=PART_LENGTH / 1000,
            dest='part_length', type=int,
            help='Length of one part in seconds (defaults to 180)')
    parser.add_argument('-c', '--cd-length', default=CD_LENGTH / 1000,
            dest='cd_length', type=int,
            help='Length of one CD in seconds (defaults to 4800)')
    parser.add_argument('-b', '--burn', action='store_true', dest='burn',
            help='Automatically burn the CDs using the `invoke` commandline.')
    parser.add_argument('--invoke', dest='invoke', metavar='COMMANDLINE',
            default='/usr/bin/brasero -p "%s" --immediately',
            help='Command line to invoke to burn the CD containing the %%s placeholder (defaults to brasero)')
    parser.add_argument('out', metavar='TEMPLATE',
            help='The brasero project file template containing %%d (the CD index)')

    args = parser.parse_args()
    if args.label is None:
        args.label = '%s - %s' % (args.artist, args.track)
        log.info('Using %r as label ...' % args.label)
    args.part_length *= 1000 # s -> ms
    args.cd_length *= 1000 # s -> ms

    # generate the brasero project files
    projects = list(build_projects(
        args.filename,
        args.artist,
        args.track,
        args.label,
        args.part_length,
        args.cd_length
    ))
    # write all project files
    for idx, project in enumerate(projects, 1):
        filename = args.out % idx
        log.info('Writing %s ...' % (filename))
        project.write(filename, 'UTF-8', True)
    # burn them?
    if args.burn:
        for idx, project in enumerate(projects, 1):
            burn_project(filename, args.invoke)
