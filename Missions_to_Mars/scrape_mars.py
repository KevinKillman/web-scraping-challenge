import requests
from bs4 import BeautifulSoup as bs4
import requests
import pymongo
from webdriver_manager.chrome import ChromeDriverManager
from splinter import Browser
import pandas as pd
from flask import Flask, render_template

# create instance of Flask app
app = Flask(__name__)

def scrape():
    url = 'https://mars.nasa.gov/news/'
    response = requests.get(url)
    soup = bs4(response.text, 'lxml')
    news_title = [x.text.strip() for x in soup.find_all('div', class_='content_title')]
    news_p = [x.text.strip() for x in soup.find_all('div', class_="rollover_description_inner")]
    title_description = []
    count= 0
    for title in news_title:
        title_description.append({'title':title, 'description':news_p[count]})
        count+=1
    
    master = {}
    master.update({'news':title_description})

    executable_path = {'executable_path': ChromeDriverManager().install()}
    browser = Browser('chrome', **executable_path, headless=False)
    url = 'https://www.jpl.nasa.gov/spaceimages/?search=&category=Mars'
    browser.visit(url)
    browser.is_text_present('Probably Not, Using for wait time', wait_time = 5)
    browser.click_link_by_id('full_image')
    browser.is_text_present('Probably Not, Using for wait time', wait_time = 5)

    soup1 = bs4(browser.html, 'html.parser')

    img = soup1.find_all('img', class_='fancybox-image')[0]

    featured_image_url = 'https://www.jpl.nasa.gov/' +img['src']


    # img = soup
    # check = True
    # try:
    #     x_img = soup.find_all('img', class_='fancybox-image')
    #     img = x_img[0]
    # except IndexError:
    #     check = False
    # if check:
    #     featured_image_url = 'https://www.jpl.nasa.gov/' + img['src']
    # if check != True:
    #     featured_image_url = 'SOMETHING WENT WRONG'
    # else:
    #     featured_image_url = 'SOMETHING WENT WRONG'
    master.update({'featured_image_url': featured_image_url})


    tables = pd.read_html('https://space-facts.com/mars/')
    me_comparison_df = tables[1]
    string = me_comparison_df.to_html()
    master.update({'html_table_string': [string]})


    url = 'https://astrogeology.usgs.gov/search/results?q=hemisphere+enhanced&k1=target&v1=Mars'
    browser.visit(url)
    soup2 = bs4(browser.html, 'html.parser')
    desc = soup2.find_all('h3')
    hemi_title = [x.text for x in desc]
    hemi_urls = []
    for title in hemi_title:
        browser.click_link_by_partial_text(title)
        browser.click_link_by_partial_text('Sample')
        hemi_urls.append({'title':title,'img_url':browser.url})
        browser.visit(url)
    master.update({'hemisphere_urls':hemi_urls})

    return master



@app.route('/scrape')
def mongo():
    result = scrape()
    x = result
    conn = 'mongodb://localhost:27017'
    client = pymongo.MongoClient(conn)
    db = client.mars_db
    db.news.drop()
    db.featured.drop()
    db.html.drop()
    db.hemi.drop()


    for k,v in result.items():
        if k == 'news':
            db.news.insert_many(v)
        if k == 'featured_image_url':
            db.featured.insert_one({k:v})
        if k == 'html_table_string':
            db.html.insert_one({k:v})
        if k == 'hemisphere_urls':
            db.hemi.insert_many(v)

    return 'scraped and inserted'



@app.route('/')
def home():

    conn = 'mongodb://localhost:27017'
    client = pymongo.MongoClient(conn)
    db = client.mars_db
    img = db.featured.find()



    return render_template('index.html', img = img)









if __name__ == "__main__":
    app.run(debug=True)
