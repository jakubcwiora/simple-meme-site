from flask import Flask

# https://demotywatory.pl/losuj -> losuje obrazek, jakoś ogarniemy żeby go postować u nasccd 

app = Flask(__name__)

@app.route("/")
def index():
  return "Azbest breton!"

app.run(host = "0.0.0.0", port=8080)