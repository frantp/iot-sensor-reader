#!/usr/bin/python3

import sys
import os


if __name__ == "__main__":
    ifile = sys.argv[1]
    ofile = sys.argv[2]
    flags = set(sys.argv[3:])
    with open(ifile, "r") as fi, open(ofile, "w") as fo:
        for line in fi:
            line = line.strip()
            if line[0] == "#":
                code, line = line.split(maxsplit=1)
                code = code[1:]
                if f"no-{code}" in flags or \
                   ("only" in flags and not code in flags):
                    continue
            fo.write(line + os.linesep)
