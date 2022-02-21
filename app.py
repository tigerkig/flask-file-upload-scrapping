import os
from flask import * 
from werkzeug.utils import secure_filename
from flask import jsonify

from asyncio.windows_events import NULL
from bs4 import BeautifulSoup 
from selenium import webdriver 
from csv import writer
import csv 
import time
import re

dir_path = os.path.dirname(os.path.realpath(__file__))
count = 0
soup =''
output_name = ''
app = Flask(__name__)  

@app.route('/')  
def upload():  
  return render_template("file_upload_form.html")  

@app.route('/run', methods = ['POST'])
def run():
   os.startfile(dir_path+ '/output/' + request.form.get('name'))
   return jsonify('complete')
   
@app.route('/success', methods = ['POST'])  
def success():
  if request.method == 'POST':
    file = request.files['file']
    if file and allowed_file(file.filename):
      file.save(os.path.join('uploads/', secure_filename(file.filename)))
      # old_name = os.path.join('uploads/', secure_filename(file.filename))
      # new_name = os.path.join('uploads/', 'input.csv')
      # os.rename(old_name, new_name)

      resp = {'name': file.filename, 'status': 0}
      return jsonify(resp)
    else:
      resp = {'name': 'You can upload only CSV files.', 'status': 1}
      return jsonify(resp)
     
@app.route('/start', methods = ['POST'])
def start():
   global soup, dir_path, output_name
   file = request.files['file']
   output_name = file.filename
   x = output_name.split('.')
   txt = x[0] + '-scrapped.' + x[1]
   file_name = dir_path + '/chromedriver'
   input_name = dir_path + '/uploads/' + file.filename
   url = "https://www.onlinecomponents.com/en"
   driver = webdriver.Chrome(file_name)
   driver.get(url)
   
   try:
      driver.find_element_by_id('main-iframe')
      time.sleep(30)
      print("ohhhhhhhhhhhhhh ----------  30 Seconds\n")
   except:
      pass

   with open(input_name) as csvfile:
      csv_reader = csv.reader(csvfile, delimiter=',')
      line_count = 0
      for row in csv_reader:
         
         if line_count > 0 :
            find_item = f'{row[1]}'
            find_brand = f'{row[2]}'.split()[0]
            selector = driver.find_element_by_name('text')
            selector.send_keys(find_item)
            button = driver.find_element_by_id('search-submit-autocomplete')
            button.click()
            
            try:
               driver.find_element_by_id('main-iframe')
               time.sleep(30)
               print("ohhhhhhhhhhhhhh ----------  30 Seconds\n")
            except:
               pass
            
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            
            ID_check = soup.find_all('div', {'class' : 'result-box w-100 py-10 py-md-4'})
            if len(ID_check):
               print("has result\n")
               has_result(find_item, find_brand)
            else:
               print("direct URL\n")
               direct_URL(find_item, find_brand)
         line_count += 1

   return jsonify({'name' : txt})
  
def has_result(find_item, find_brand):
    global count, soup
    count += 1
    delivery = ''
    time.sleep(5)
    search_result = soup.find_all('div', {'class' : 'result-box w-100 py-10 py-md-4'})
    for search in search_result:
        title = search.find('h3', {'class' : 'text-uppercase mb-0 product-title'})
        all_brand = search.find('h6', {'class' : 'text-uppercase mb-0 product-brand'})
        brand = all_brand.text.strip().split()
        
        if title.text == find_item and brand[0].lower() == find_brand.lower():
            quantity = search.find('div', {'class' : 'col-4 font-weight-600 pl-lg-10 pr-5'})
            all_price = search.find('ul', {'class' : 'text-oxford-blue font-size-14'})
            price = all_price.find('div', {'class' : 'col-8'})
            supplier_description = search.find('p', {'class' : 'font-size-13 d-none d-md-block mb-11 product-description'})

            all_list = search.find_all('li', {'class' : 'mb-5 mb-md-16'})
            
            for val in all_list:
                try:
                    val['style']
                except:
                    is_check = val.find('span', {'class', 'title'})
                    if is_check.text == 'In Stock:':
                        stock = val.find('span', {'class', 'value'})
                    else:
                        delivery = delivery + val.text.strip() + '; '
            row = [count, title.text, all_brand.text.strip(), '', quantity.text.strip(), price.text.strip(), stock.text.strip(), delivery,supplier_description.text.strip()]
            write_to_csv(row)
      
def direct_URL(find_item, find_brand):
    global count, soup
    count += 1
    delivery = ''
    time.sleep(5)
    title = soup.find('h1', {'class' : 'text-uppercase text-olc-blue mb-0 text-center text-lg-left pt-10'}).text.strip()
    all_brand = soup.find('a', {'class' : 'productManuLink'})
    brand = all_brand.text.strip().split()
    
    if title == find_item and brand[0].lower() == find_brand.lower():
       
        stock = soup.find('span', {'class' : 'value Instock-availability Instock-availability-red text-uppercase'})
        supplier_description = soup.find('p', {'class' : 'text-graphite-dark font-size-16 mb-8'})
        divPriceListLeft = soup.find('div', {'id' : 'divPriceListLeft'})
        price_quantity = divPriceListLeft.find('div', {'class' : 'row border-bottom px-25 py-5'})
        quantity = price_quantity.find('span', {'class' : 'hdbreak'})
        price = price_quantity.find('div', {'class' : 'col-4 text-right'})
        
        delivery_date = soup.find('div', {'id' : 'tbAvailability'})
        delivery_list = delivery_date.find_all('div', {'class' : 'row border-bottom py-5 px-25'})
        for val in delivery_list:
            try:
                val['style']
            except:
                string = re.sub('\n', '', val.text.strip())
                str = re.sub(' +', ' ', string)
                delivery = delivery + str + '; '
        
        row = [count, title, all_brand.text.strip(), '', quantity.text.strip(), price.text.strip(), stock.text.strip(), delivery,supplier_description.text.strip()]
        write_to_csv(row)
    else:
        print('Cannot find search value')
        
def write_to_csv(list_of_elem):
   print(list_of_elem)
   global dir_path, count , output_name
   x = output_name.split('.')
   txt = x[0] + '-scrapped.' + x[1]
   name = dir_path + '/output/' + txt
   header = ['Position', 'Item', 'Brand', 'Description', 'Quantity', 'Price', 'Stock', 'Delivery', 'Supplier Description']
   with open(name, 'a+', newline='') as write_obj:
      csv_writer = writer(write_obj)
      if count == 1:
         csv_writer.writerow(header)
      csv_writer.writerow(list_of_elem)

def allowed_file(filename):
   if filename.rsplit('.', 1)[1].lower() == 'csv':
      return True
   else:
      return False
  
if __name__ == '__main__':  
    app.run(host= '0.0.0.0', debug = True)