import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from selectorlib import Extractor
import requests 
import json 
from time import sleep
import pandas as pd


def send_email(receiver_address, mail_content, item_name):
    
    #Setup the MIME
    message = MIMEMultipart()
    message['From'] = sender_address
    message['To'] = receiver_address

    #The subject line
    message['Subject'] = item_name+' has reached target price' 

    #The body and the attachments for the mail
    message.attach(MIMEText(mail_content, 'plain'))

    #Create SMTP session for sending the mail
    session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
    session.starttls() #enable security
    session.login(sender_address, sender_pass) #login with mail_id and password
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()
    print('Mail Sent')




# Create an Extractor by reading from the YAML file
e = Extractor.from_yaml_file('modules/selectors.yml')

def scrape(url):  

    headers = {
        'dnt': '1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'referer': 'https://www.amazon.com/',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }

    # Download the page using requests
    # print("Downloading %s"%url)
    r = requests.get(url, headers=headers)
    # Simple check to check if page was blocked (Usually 503)
    if r.status_code > 500:
        if "To discuss automated access to Amazon data please contact" in r.text:
            print("Page %s was blocked by Amazon. Please try using better proxies\n"%url)
        else:
            print("Page %s must have been blocked by Amazon as the status code was %d"%(url,r.status_code))
        return None
    text = e.extract(r.text)
    price = text['price']
    item = text['name']
    # Pass the HTML of the page and create 
    # return e.extract(r.text)
    return item, price


def amazon_auto_check_price(receiver_address, refresh_freq_sec, print_record=False):
    product = pd.read_csv('product.csv')
    URL = product['item_link']
    TARGET_PRICE = product['target_price']
    RE_RUN_SEC = refresh_freq_sec
    while True:
        for url, target_price in zip(URL, TARGET_PRICE):
            item_name, price = scrape(url=url)
            if price == None:
                if print_record==True:
                    print (f'{item_name} out of stock')
                continue
            elif float(price[1::]) <= target_price:
                break
                mail_content = f'ULR: {url}'
                send_email(receiver_address, mail_content, item_name)
            if print_record==True:
                print(f'{item_name} Target Price Not Reach')
        if print_record==True:
            print(f're-run in {RE_RUN_SEC/60} minutes')
        sleep(RE_RUN_SEC)