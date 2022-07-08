"""
A CLI e-book manager for Amazon Kindle devices.

Usage:
  bkmgr add <path>
  bkmgr sync 
  bkmgr upload <book> [-d]
  bkmgr list

Options:
  -h --help     Show this screen
  --version     Show version
"""
from docopt import docopt
from commands import add, list_, sync_, upload

if __name__ == '__main__':
    arguments = docopt(__doc__, version='bkmgr 1.0')
    if arguments.get('add', False) is True:
        add(arguments.pop('<path>'))
    elif arguments.get('list', False) is True:
        list_()
    elif arguments.get('sync', False) is True:
        sync_()
    elif arguments.get('upload', False) is True:
        upload(arguments.pop('<book>'), dry_run=arguments.pop('-d'))
