from bs4 import BeautifulSoup
import requests


# URL of targeted website
demot = "https://demotywatory.pl/losuj"

def getImages(number = 1):
  images = []
  for i in range(number):  
    response = requests.get(demot)
    if response.status_code == 200:
      html = BeautifulSoup(response.content, 'html.parser')
      img = html.find('span', class_ = 'picwrapper').find('img')
      img_src = img['src']
      img_alt = img.get('alt', '')  # fallback if alt missing
      images.append([img_src, img_alt])
  
    else:
      print(f"Failed to fetch: {response.status_code}")
    
  return images