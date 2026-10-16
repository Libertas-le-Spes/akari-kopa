import sys

from merge_requests.entrypoints.cli.main import main

sys.exit(main(sys.argv[1:]))
