import string
import sys

from state import *
from tmsim import *

if __name__ == "__main__":
    name = sys.argv[-1]
    fileName = name + ".tm4"
    path = "../tm4_files/" + fileName
    
    try:
        assert len(sys.argv) > 1
        for flag in sys.argv[2:-1]:
            if not (flag in ["-q", "-s", "-f"]):
                int(flag)
    
    except:
        raise Exception("Usage: python tm4_simulator.py [-q] [-s] [# steps before aborting] [-f] [name of TM4 file]\n \
            Enable -q if you want no program output\n \
            Enable -l if you want limited program output\n \
            Enable -s followed by the max number of steps if you want to stop interpreting after a certain number of commands\n \
            Enable -f if you want to dump the history into a file in tm4_histories instead of the standard output.")
        
    sttm = SingleTapeTuringMachine(path, ["_", "1", "H", "E"])
    args = sys.argv[1:-1]

    quiet = ("-q" in args)

    limited = ("-l" in args)

    numSteps = sys.maxint
    if ("-s" in args):
        numSteps = args[args.index("-s") + 1]

    output = None
    if ("-f" in args):
        output = open("../tm4_histories/" + name + "_history.txt", "w")
        
        try:
            assert "-s" in args
        except:
            raise Exception("You can't include the -f flag without also specifying a maximum step count with the -s flag!")

    sttm.run(quiet, numSteps, output)


