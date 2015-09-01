import sys
import json
import requests
from bs4 import BeautifulSoup
import urllib3


    
def cardinfo(cardname, setabbr):
    
    mtgapiurl = 'http://api.mtgapi.com/v2/cards?name={}&set={}'.format(cardname, setabbr)
    
    page = requests.get(mtgapiurl)
    if page.raise_for_status() is not None: # the request failed
        return ["The API request failed"]
    page = page.json()['cards']
    if page is None: #something got entered incorrectly
        return ["Uh oh, something went wrong. Check both your name and set code and try again"]
    else:
        if setabbr == 'MM2':
            setname = 'Modern Masters 2015' #edge case 1
        elif setabbr == 'CMD':
            setname = 'Commander'
        else:
            setnameurl = 'http://api.mtgapi.com/v2/sets?code=' + setabbr
            setname = requests.get(setnameurl).json()['sets'][0]['name']
    cardname = page[0]['name']
    return [cardname, setname]

# Gets the current USD to EUR exchange rate
def getexchangerate():
    url = 'https://www.bitstamp.net/api/eur_usd/'
    page = requests.get(url)
    rates = page.json()['buy']   
    return rates
    
def getmkmprice(cardname, setcode): #Gets the current price from MagicCardMarket

    
    
    file = open('mkmnames.json')
    str = file.read()
    mkmnames = json.loads(str)

    setname = mkmnames[setcode]
    mkmbase = 'https://www.magiccardmarket.eu/Products/Singles/{}/{}'.format(setname, cardname)

    mkmbase = mkmbase.replace("'", "%27")
    mkmbase = mkmbase.replace(" ", "+") #complete the magiccardmarket.eu url

    mkmpage = requests.get(mkmbase)
    mkmsoup = BeautifulSoup(mkmpage.text, "html.parser")
    price = mkmsoup.find("span", {"itemprop":"lowPrice"}).getText()
    return price

def getmtggoldfishprices(cardname, setname): # Gets current prices from several vendors
    
    
    goldfishurl = 'http://www.mtggoldfish.com/price/{}/{}'.format(setname, cardname)
    
    goldfishurl = goldfishurl.replace("'", "")
    goldfishurl = goldfishurl.replace(",", "")
    goldfishpage = requests.get(goldfishurl)
    gfsoup = BeautifulSoup(goldfishpage.text, "html.parser")
    
    prices = []    
    sellprices = gfsoup.find_all(attrs={"class": "btn-shop btn btn-default price-card-purchase-button btn-paper-muted"})
    
    
    tcgneeded = True
    abuneeded = True
    ckneeded = True
    cfbneeded = 0
    tcgmid = None
    for entry in sellprices:
        if "TCGplayer Mid" in entry.text:
            if tcgneeded: 
                tcgm = entry.find("span", {"class":"btn-shop-price"}).text
                tcgm = 'TCG Mid: ' + tcgm[3:]             
                tcgneeded = False          
                tcgmid = tcgm
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
    if tcgmid is not None:
        prices.insert(0, tcgmid)
    return prices
    
def strikezone(cardname, setname, sell):
    cardname = cardname.replace(",", "")
    if setname == "Future Sight":
        setname = "Futuresight" #edge case
    if sell:
        szurl = 'http://shop.strikezoneonline.com/TUser?T={}%20{}&MC=CUSTS&MF=B&BUID=637&ST=D&CMD=Search'.format(cardname, setname)
    else:
        szurl = 'http://shop.strikezoneonline.com/TUser?T={}%20{}&MC=CUSTS&MF=B&BUID=637&ST=D&M=B'.format(cardname, setname)
    
    strikezonepage = requests.get(szurl)
    szsoup = BeautifulSoup(strikezonepage.text, "html.parser")
    pricetable = szsoup.find('table', attrs={'class':'ItemTable'})
    
    if pricetable is None:
        return 'Not found'
    pricetablerows = pricetable.find_all('tr')
    
    for entry in pricetablerows:  
        if "Near Mint Normal English" in entry.text:
            price = entry.find("span").text
            if sell:
                return 'StrikeZone: $ {}'.format(price)
            else:
                return 'StrikeZone Buylist: $ {}'.format(price)
    
    return 'Not found'
        
        
def scrape(cardname, setcode):
    info = cardinfo(cardname, setcode)
    
    if len(info) == 1:
        info = info[0]
        ''.join(info)
        return [info]
    cardname = info[0]
    setname = info[1]
    print(info)
    prices = []
    
    goldfishprices = getmtggoldfishprices(cardname, setname)
    
    mkmprice = getmkmprice(cardname, setcode)
    
    mkmUSD = mkmprice.replace(",", ".")
    mkmUSD = float(mkmUSD)
    mkmUSD = float(getexchangerate()) * mkmUSD    
    mkmUSDprice = 'Magiccardmarket in USD: $' + "{:.2f}".format(mkmUSD) 
    mkmprice = 'Magiccardmarket: {} euros'.format(mkmprice)
    
    prices = goldfishprices
    
    szsell = strikezone(cardname, setname, True)
    szbuy = strikezone(cardname, setname, False)
    
    if szbuy != 'Not found':
        prices.append(szbuy)
    if szsell != 'Not found':
        prices.insert(1, szsell)
      
    prices.insert(0, mkmUSDprice)
    prices.insert(0, mkmprice)
    
    
    return prices

if __name__ == "__main__":
    scrape(sys.argv)