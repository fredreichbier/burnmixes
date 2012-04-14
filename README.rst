burnmixes
=========

A simple stupid Python 2.7 script to burn long MP3 files with Brasero. It automatically
splits the file in same-sized chunks (for easy skipping) and creates as many project files
as needed (one per CD).

Dependencies
------------

 * `pymad`
 * If you're not using Python 2.7, you have to install `argparse`.
 * Brasero, if you want to burn real CDs at least.

Usage
-----

:: 

    usage: burnmixes.py [-h] -a ARTIST -t TRACK [-l LABEL] [-p PART_LENGTH]
                        [-c CD_LENGTH] [-b] [--invoke COMMANDLINE]
                        FILENAME TEMPLATE

    Burn looooong MP3 files on CDs.

    positional arguments:
      FILENAME              The MP3 file to burn
      TEMPLATE              The brasero project file template containing %d (the
                            CD index)

    optional arguments:
      -h, --help            show this help message and exit
      -a ARTIST, --artist ARTIST
                            Artist's name
      -t TRACK, --track TRACK
                            The track name template containing %d -- it will be
                            replaced with the track ID
      -l LABEL, --label LABEL
                            The label template containing %d (the CD index). Can
                            be automatically constructed from the artist and track
      -p PART_LENGTH, --part-length PART_LENGTH
                            Length of one part in seconds (defaults to 180)
      -c CD_LENGTH, --cd-length CD_LENGTH
                            Length of one CD in seconds (defaults to 4800)
      -b, --burn            Automatically burn the CDs using the `invoke`
                            commandline.
      --invoke COMMANDLINE  Command line to invoke to burn the CD containing the
                            %s placeholder (defaults to brasero)

Example
-------

::

    python2 burnmixes.py -b -a "Some Artist" -t "Some Mix Track %d" \
                         -c 2000 -p 360 some-very-long.mp3 \
                         my-project-%d.brasero

Caveats
-------

If you're using Brasero, it might spend a giant amount of time trying to normalize the tracks.
To avoid that, you can deactivate the Normalize plugin.

License
-------

burnmixes.py is licensed under the GNU GPLv3.
