from decimal import Decimal
import sys
import json
import requests
from bs4 import BeautifulSoup
import urllib3

    
def cardinfo(cardname, setabbr):
    mtgapiurl = 'http://api.mtgapi.com/v2/cards?name='
    mtgapiurl += cardname
    mtgapiurl += '&set='
    mtgapiurl += setabbr
    page = requests.get(mtgapiurl).json()['cards']
    if page is None: #something got entered incorrectly
        return []
    else:
        setnameurl = 'http://api.mtgapi.com/v2/sets?code=' + setabbr
        setname = requests.get(setnameurl).json()['sets'][0]['name']
        cardname = page[0]['name']
        return [cardname, setname]

# Gets the current USD to EUR exchange rate
def getexchangerate():
    url = 'https://openexchangerates.org/api/latest.json?app_id=33c58ff9ceb84f04ae7f737a00026bbf'
    page = requests.get(url).json()
    rates = page['rates']
    rate = rates['EUR']
    return rate
    
def getmkmprice(cardname, setcode): #Gets the current price from MagicCardMarket

    mkmbase = 'https://www.magiccardmarket.eu/Products/Singles/'
    
    file = open('mkmnames.json')
    str = file.read()
    mkmnames = json.loads(str)
    
    setname = mkmnames[setcode.upper()]
    mkmbase += setname + "/"
    mkmbase += cardname
    mkmbase = mkmbase.replace("'", "%27")
    mkmbase = mkmbase.replace(" ", "+") #complete the magiccardmarket.eu url

    mkmpage = requests.get(mkmbase)
    mkmsoup = BeautifulSoup(mkmpage.text, "html.parser")
    price = mkmsoup.find("span", {"itemprop":"lowPrice"}).getText()
    return price
    
def getmtggoldfishprices(cardname, setname): # Gets the current price from TcgPlayer and ChannelFireball
    goldfishurl = 'http://www.mtggoldfish.com/price/'
    goldfishurl += setname
    goldfishurl += '/' + cardname
    goldfishurl = goldfishurl.replace("'", "")
    goldfishpage = requests.get(goldfishurl)
    gfsoup = BeautifulSoup(goldfishpage.text, "html.parser")
    
    both = gfsoup.find_all(attrs={"class": "btn-shop btn btn-default price-card-purchase-button btn-paper-muted"}) #tcgplayer-3, 
    
    tcgm = both[3]
    tcgm = tcgm.find("span", {"class":"btn-shop-price"}).text
    endbracket = tcgm.find('>')
    tcgm = 'TCG Mid: ' + tcgm[:endbracket]
    
    cfbprice = both[1]
    cfbprice = cfbprice.find("span", {"class":"btn-shop-price"}).text
    endbracket = cfbprice.find('>')
    cfbprice = 'Channel Fireball: ' + cfbprice[:endbracket]
    return [cfbprice, tcgm]
    
def main(args):
    
    cardname = args[1]
    setcode = args[2]
    
    info = cardinfo(cardname, setcode)
    if len(info) < 1:
        return ["Uh oh, something went wrong. Check both your name and set code and try again"]
    cardname = info[0]
    setname = info[1]
    
    
    goldfishprices = getmtggoldfishprices(cardname, setname)
    mkmprice = getmkmprice(cardname, setcode)
    
    mkmUSD = mkmprice.replace(",", ".")
    mkmUSD = float(mkmUSD)
    mkmUSD = mkmUSD / getexchangerate()
    
    mkmUSDprice = 'Magiccardmarket in USD: $' + "{:.2f}".format(mkmUSD) 
    
    mkmprice = 'Magiccardmarket: €' + mkmprice
    print([mkmprice, mkmUSDprice])
    cfbprice = goldfishprices[0]
    tcgm = goldfishprices[1]
    
    
    prices = [mkmprice, mkmUSDprice, cfbprice, tcgm]
    
    return prices

if __name__ == "__main__":
    main(sys.argv)
