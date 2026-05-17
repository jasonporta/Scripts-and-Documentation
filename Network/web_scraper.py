#!/usr/bin/python3

import requests
from bs4 import BeautifulSoup

url = 'https://www.ebi.ac.uk/emdb'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Extract data, e.g., all the links on the page
links = soup.find_all('a')
for link in links:
    print(link.get('href'))
