# -*- coding: utf-8 -*-
import code
import sys

from pykdump.API import *


code.interact(
    banner=(
        'PyKdump Embedded REPL: Python {}\n'
        'Use Ctrl-D to return to crash\n\n'
        'from pykdump.API import *\n'
    ).format(sys.version),
    local=locals(),
    exitmsg='Returning to crash',
)
