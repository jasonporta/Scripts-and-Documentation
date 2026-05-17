#!/usr/bin/python

import shutil

total, used, free = shutil.disk_usage(__file__)

total = total/pow(10,9)
used = used/pow(10,9)
free = free/pow(10,9)

total2 = '{:.1f}'.format(total)
used2 = '{:.1f}'.format(used)
free2 = '{:.1f}'.format(free)

print('\n Total space:', total2, '\n', 'Amount used:', used2, '\n', 'Amount free:', free2, '\n')
