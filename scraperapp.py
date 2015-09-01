import script
from flask import Flask
from flask import request
from flask import render_template

app = Flask(__name__)
 

@app.route('/')
def index():
    return render_template('index.html')
 
@app.route('/prices', methods = ['POST'])
def signup():
    card = request.form['card']
    set = request.form['set']
    prices = script.scrape(card, set.upper())
    return render_template('cards.html', card=card, prices=prices)
    
    

if __name__ == "__main__":
    app.run()