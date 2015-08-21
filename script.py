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
    page = requests.get(mtgapiurl)
    if page.raise_for_status() is not None: # the request failed
        return ["The API request failed"]
    page = page.json()['cards']
    if page is None: #something got entered incorrectly
        return ["Uh oh, something went wrong. Check both your name and set code and try again"]
    else:
        if setabbr.upper() == 'MM2':
            setname = 'Modern Masters 2015' #edge case
        else:
            setnameurl = 'http://api.mtgapi.com/v2/sets?code=' + setabbr
            setname = requests.get(setnameurl).json()['sets'][0]['name']
    cardname = page[0]['name']
    return [cardname, setname]

# Gets the current USD to EUR exchange rate
def getexchangerate():
    #url = 'https://openexchangerates.org/api/latest.json?app_id=33c58ff9ceb84f04ae7f737a00026bbf'
    url = 'https://www.bitstamp.net/api/eur_usd/'
    page = requests.get(url)
    rates = page.json()['buy']   
    return rates
    
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

def allindices(string, sub):
    listindex = []
    offset = 0
    i = string.find(sub, offset)
    while i >= 0:
        listindex.append(i)
        i = string.find(sub, i + 1)
    return listindex
    
def getmtggoldfishprices(cardname, setname): # Gets current prices from several vendors
    cardname = cardname.replace("'", "")
    goldfishurl = 'http://www.mtggoldfish.com/price/'
    goldfishurl += setname
    goldfishurl += '/' + cardname
    goldfishurl = goldfishurl.replace("'", "")
    goldfishpage = requests.get(goldfishurl)
    gfsoup = BeautifulSoup(goldfishpage.text, "html.parser")
    
    prices = []
   
    
    #sellprices = gfsoup.find_all(attrs={"class": "price-card-sell-prices"})
    sellprices = gfsoup.find_all(attrs={"class": "btn-shop btn btn-default price-card-purchase-button btn-paper-muted"})
    
    
    tcgneeded = True
    abuneeded = True
    ckneeded = True
    cfbneeded = 0
    for entry in sellprices:
        if "TCGplayer Mid" in entry.text:
            if tcgneeded: 
                tcgm = entry.find("span", {"class":"btn-shop-price"}).text
                tcgm = 'TCG Mid: ' + tcgm[3:]             
                tcgneeded = False          
                prices.append(tcgm)
        if "Channel Fireball" in entry.text:          
            if cfbneeded == 0:  
                cfbprice = entry.find("span", {"class":"btn-shop-price"}).text
                cfbprice = 'Channel Fireball: ' + cfbprice[3:]
                prices.append(cfbprice)
            if cfbneeded == 3:
                cfbprice = entry.find("span", {"class":"btn-shop-price"}).text
                cfbprice = 'Channel Fireball Buylist: ' + cfbprice[3:]
                cfbneeded += 1
                prices.append(cfbprice)
            cfbneeded += 1
        if "ABU Games" in entry.text:
            if abuneeded: 
                abu = entry.find("span", {"class":"btn-shop-price"}).text
                abu = 'ABU Games Buylist: ' + abu[3:]             
                abuneeded = False          
                prices.append(abu)
        if "Card Kingdom" in entry.text:
            if ckneeded: 
                ck = entry.find("span", {"class":"btn-shop-price"}).text
                ck = 'Card Kingdom Buylist: ' + ck[3:]             
                ckneeded = False          
                prices.append(ck)
    
    return prices
    
def scrape(cardname, setcode):
    info = cardinfo(cardname, setcode)
    
    if len(info) == 1:
        info = info[0]
        ''.join(info)
        return [info]
    cardname = info[0]
    setname = info[1]
    
    prices = []
    goldfishprices = getmtggoldfishprices(cardname, setname)
    
    mkmprice = getmkmprice(cardname, setcode)
    
    mkmUSD = mkmprice.replace(",", ".")
    mkmUSD = float(mkmUSD)
    mkmUSD = float(getexchangerate()) * mkmUSD
    
    mkmUSDprice = 'Magiccardmarket in USD: $' + "{:.2f}".format(mkmUSD) 
    mkmprice = 'Magiccardmarket: ' + mkmprice + ' euros'
    
    prices = goldfishprices
    
    prices.insert(0, mkmUSDprice)
    prices.insert(0, mkmprice)
    
    return prices

