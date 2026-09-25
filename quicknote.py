import argparse
import sys

# --------------------------------------------------------------------------
# this printes full help (not just a usage line) on any error,
# example: when a required argument is missing.
# --------------------------------------------------------------------------
class HelpOnErrorParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write(f"error: {message}\n\n")
        self.print_help()
        sys.exit(2)

def build_praser():
    parser = HelpOnErrorParser(
        prog="quicknote.py",
        description="A simple JSON-backed command-line todo list manager.",
        epilog=(
            ""
                ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(
        dest="command", metavar="{}",
        parser_class=HelpOnErrorParser
    )

    return parser

# --------------------------------------------------------------------------
# Main Function
# --------------------------------------------------------------------------
def main():
    parser = build_praser()
    args = parser.parse_args()

    if not getattr(args, "command", None):
        parser.print_help()
        sys.exit(0)

    args.func(args)

if __name__ == "__main__":
    main()