from flask import Flask
from flask import request
from flask import render_template
import sys
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import PhantomJS

import urllib3
from pyvirtualdisplay import Display
from flask import request, redirect
from ghost import Ghost


app = Flask(__name__)
 
prices = []
 
@app.route('/')
def index():
    return render_template('index.html')
 
@app.route('/prices', methods = ['POST'])
def signup():
    card = request.form['card']
    set = request.form['set']
    things = ["", card, set]
    price = scraper(things)
    prices = price
    print(price) 
    return render_template('cards.html', card=card, prices=prices)
    


def scraper(args):
    file = open('mkmnames.json')
    str = file.read()
    mkmnames = json.loads(str)

    cardname = args[1]
    set = args[2]
    
    mcibase = "http://www.magiccards.info/"
    mkmbase = 'https://www.magiccardmarket.eu/Products/Singles/'
    
    
    setnumurl = 'http://mtgscavenger.com/api/lookup?card%5B%5D=' # the base url to look up the set number
    setnumurl += set + '='
    setnumurl += cardname
    setnumurl = setnumurl.replace(" ", "%20")
    setnumurl = urllib3.PoolManager().request('GET', setnumurl).read() #opens the set number page
    
    setnumurl = json.loads(setnumurl.decode('utf-8'))[0] #parses it into readable json
    
    
    setnum = setnumurl['number'] #access the set number
    cardname = setnumurl['card_name'] #account for typos
    
    mcibase += setnumurl['official_set_code'].lower() #grabs the offical set code and treats it as lowercase
    mcibase += '/en/' 
    mcibase += setnum
    mcibase += '.html' # complete the magiccards.info url
    
    
    setname = mkmnames[set.upper()]
    mkmbase += setname + "/"
    mkmbase += cardname
    mkmbase = mkmbase.replace("'", "%27")
    mkmbase = mkmbase.replace(" ", "+") #complete the magiccardmarket.eu url

    
    mkmurl = mkmbase
    mkmpage = requests.get(mkmurl)
    mkmsoup = BeautifulSoup(mkmpage.text, "html.parser")
    price = mkmsoup.find("span", {"itemprop":"lowPrice"}).getText()
    mkmprice = 'Magiccardmarket.eu: ' + price    
    
    
    cfbpriceurl = 'http://magictcgprices.appspot.com/api/cfb/price.json?cardname='
    cfbpriceurl += cardname
    cfbpriceurl += '&setname=' + setname
    cfbprice = requests.get(cfbpriceurl).text
    cfbprice = cfbprice.replace("[", "")
    crbprice = cfbprice.replace("]", "")  
    cfbprice = "CFB: " +  crbprice
    
    fulurl = 'http://www.mtggoldfish.com/price/Khans+of+Tarkir/Polluted+Delta#online'
    goldfishurl = 'http://www.mtggoldfish.com/price/'
    goldfishurl += setnumurl['set_name']
    goldfishurl += '/' + cardname
    goldfishurl = goldfishurl.replace("'", "")
    goldfishpage = requests.get(goldfishurl)
    gfsoup = BeautifulSoup(goldfishpage.text, "html.parser")
    
    tcgm = gfsoup.find_all(attrs={"class": "btn-shop btn btn-default price-card-purchase-button btn-paper-muted"})[2]
    tcgm = tcgm.find("span", {"class":"btn-shop-price"}).text
    startbracket = tcgm.find('>')
    tcgm = 'TCG Mid: ' + tcgm[:startbracket]
    
    prices = [mkmprice, cfbprice, tcgm]
    """
    
    display.start()
    driver = webdriver.Firefox() ##look up headless testing
    driver.get(mcibase)
    tcghigh = driver.find_element_by_class_name("TCGPHiLoHigh")
    tcgmid = driver.find_element_by_class_name("TCGPHiLoMid")
    tcglow = driver.find_element_by_class_name("TCGPHiLoLow")
    driver.close() 
    display.stop()
    prices = [mkmprice, tcghigh.text, tcgmid.text, tcglow.text]
    #prices = [tcghigh.text, tcgmid.text, tcglow.text]"""
    
    return prices
    #print(mkmprice)
    #print(tcghigh.text)
    #print(tcgmid.text)
    #print(tcglow.text)
    

if __name__ == "__main__":
    app.run()