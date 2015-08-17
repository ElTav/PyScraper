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
    things = ["", card, set]
    prices = scraper(things)
    return render_template('cards.html', card=card, prices=prices)
    
    

if __name__ == "__main__":
    app.run()