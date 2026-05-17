#!/usr/bin/python

import re
from typing import List


def main(
    text: str = "Example of text with several numbers formats \n Jonathon Doe \n 1234 America Dr, \n Detroit, MI 48127, USA \n 313-248-9218 \n 313-131-5612 ") -> List[str]:
    phoneRegex = re.compile(
        r"""(
        (\d{3}|\(\d{3}\))?                 # area code
        (\s|-|\.)?                         # separator
        (\d{3})                            # first 3 digits
        (\s|-|\.)                          # separator
        (\d{4})                            # last 4 digits
        (\s*(ext|x|ext.)\s*(\d{2,5}))?     # extension
        )""",
        re.VERBOSE,
    )

    matches = []
    for numbers in phoneRegex.findall(text):
        matches.append(numbers[0])

    return matches
