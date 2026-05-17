#!/usr/bin/python3

import string
import random

def randompassword():
   chars = string.ascii_uppercase + string.ascii_lowercase + string.digits + string.punctuation
   size = random.randint(10, 12)
   return ''.join(random.choice(chars) for x in range(size))

print(randompassword())
