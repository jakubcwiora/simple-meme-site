from bs4 import BeautifulSoup
from time import sleep
from flask import Flask, request, jsonify
import requests

webhook = "your.url"

# URL of targeted website
demot = "https://demotywatory.pl/losuj"

def getImages(number = 1):
  images = []
  for i in range(number):  
    response = requests.get(demot)
    if response.status_code == 200:
      html = BeautifulSoup(response.content, 'html.parser')
      img = html.find('span', class_ = 'picwrapper').find('img')
      images.append(img['src'])
  
    else:
      print(f"Failed to fetch: {response.status_code}")
    
    sleep(3)
  return images


while True:
  
  message = getImages(1)
  r = requests.post(webhook, data = {"content": message})
  


# app = Flask("GetDemotivated")

# @app.route('/')
# def home():
#   return 



print(getImages(1))
