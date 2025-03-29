import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv

#Chrome options
options = uc.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = uc.Chrome(options=options)

#List of cities
city_urls = [
  "https://www.cardekho.com/used-cars+in+new-delhi",
  "https://www.cardekho.com/used-cars+in+mumbai",
  "https://www.cardekho.com/used-cars+in+bangalore",
  "https://www.cardekho.com/used-cars+in+chennai",
  "https://www.cardekho.com/used-cars+in+hyderabad",
  "https://www.cardekho.com/used-cars+in+pune",
  "https://www.cardekho.com/used-cars+in+kolkata",
  "https://www.cardekho.com/used-cars+in+ahmedabad",
  "https://www.cardekho.com/used-cars+in+jaipur",
  "https://www.cardekho.com/used-cars+in+lucknow"
]

#Open CSV file to save data
with open("used_cars_data.csv", "w", newline="", encoding="utf-8") as file:
  writer = csv.writer(file)
  writer.writerow(["City", "Car Name", "Price", "Year", "Mileage", "Fuel Type", "Transmission", "Car URL"])
  for city_url in city_urls:
    driver.get(city_url)
    city_name = city_url.split("+in+")[1].replace("-", " ").title()
    print(f"\n🚗 Scraping data from: {city_name}")

  #Wait for cars to load
    try:
      WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "gsc_col-xs-12")))
    except:
      print("No car listings found. Skipping...")
      continue

    #Scrolling time(max 10)
    scroll_attempts = 0
    previous_car_count = 0

    for _ in range(10):
      last_height = driver.execute_script("return document.body.scrollHeight")
      driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
      time.sleep(5)

      new_height = driver.execute_script("return document.body.scrollHeight")
      print(f"Scrolled: Previous height = {last_height}, New height = {new_height}")

      #Count car elements
      cars = driver.find_elements(By.CLASS_NAME, "gsc_col-xs-12")
      if len(cars) == previous_car_count:
        print(f"No new cars loaded after scrolling. Stopping...")
        break
      previous_car_count = len(cars)

      print(f"Found {len(cars)} total cars in {city_name}")

      #Details from all cars
      for index, car in enumerate(cars):
        try:
          #Car Name & URL
          car_name = car.find_element(By.TAG_NAME, "h3").text.strip()
          car_url = car.find_element(By.TAG_NAME, "a").get_attribute("href")

          #Price
          try:
            price = car.find_element(By.CLASS_NAME, "Price").text.strip()
          except:
            price = "Price not available"

          #Year, Mileage, Fuel Type, Transmission
          try:
            details = car.find_element(By.CLASS_NAME, "dotsDetails").text.strip().split("•")
            year = details[0].strip() if len(details) > 0 else "N/A"
            mileage = details[1].strip() if len(details) > 1 else "N/A"
            fuel_type = details[2].strip() if len(details) > 2 else "N/A"
            transmission = details[3].strip() if len(details) > 3 else "N/A"
          except:
            year, mileage, fuel_type, transmission = "N/A", "N/A", "N/A", "N/A"

          #Print data
            print(f"   {index+1}. {car_name} | {price} | {year} | {mileage} | {fuel_type} | {transmission} | {car_url}")

          #Save to CSV
            writer.writerow([city_name, car_name, price, year, mileage, fuel_type, transmission, car_url])
        except Exception as e:
          print(f"Error extracting car details: {e}")

driver.quit() #Close the browser
print("\nScraping Successful")

#-----------------------Load Dataset and Clean----------------------------
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')
import re

df = pd.read_csv('used_cars_data.csv')

#drop transmission column
df.drop('Transmission', axis=1, inplace=True)
df.drop('Car URL', axis=1, inplace=True)

#Rename Fuel Type to Transmission
df.rename(columns={'Fuel Type': 'Transmission'}, inplace=True)
df.rename(columns={'Mileage': 'Fuel_Type'}, inplace=True)
df.rename(columns={'Year': 'Mileage'}, inplace=True)
df.rename(columns={'Car Name': 'Car_Name'}, inplace=True)

# drop null values from Transmission
df.dropna(subset=['Transmission'], inplace=True)

# Extract first 4 digits of year from Car Name and feed to a new column "Year"
df['Year'] = df['Car_Name'].str.extract(r'(\d{4})')

#Clean noise and convert the Price column
def clean_price(price):
    price = re.sub(r"[₹,\n]|Compare", "", price).strip()
    
    if "Lakh" in price:
        price = price.replace("Lakh", "").strip()
        return int(float(price) * 100000)
    elif "Crore" in price:
        price = price.replace("Crore", "").strip()
        return int(float(price) * 10000000)
    else:
        return None

#Apply function
df["Price"] = df["Price"].apply(clean_price)

#Remove the starting year from car names
def clean_car_name(name):
    return re.sub(r"^\d{4} ", "", name).strip()

#Apply function
df["Car_Name"] = df["Car_Name"].apply(clean_car_name)

#Remove noise from Mileage
df["Mileage"] = df["Mileage"].str.replace("kms", "").astype(str)
df["Mileage"] = df["Mileage"].str.replace(",", "").astype(float)

# convert year into int
df['Year'] = df['Year'].astype(int)

#saved the cleaned data into new csv file 
df.to_csv("cleaned_used_cars_data.csv", index=False, encoding="utf-8")

import mysql.connector
import pandas as pd
connection = mysql.connector.connect(host='localhost', user='root', password="GKB@mysql_ds07", database='code_it') 
cursor = connection.cursor()

df = pd.read_csv('cleaned_used_cars_data.csv')
#insert into MySQL table
for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO cleaned_used_cars_data (City, Car_Name, Price, Mileage, Fuel_Type, Transmission, Year)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (row["City"], row["Car_Name"], row["Price"], row["Mileage"], row["Fuel_Type"], row["Transmission"], row["Year"]))

connection.commit()
print("Data inserted successfully")

querry = "SELECT * FROM cleaned_used_cars_data"
cursor.execute(querry)
rows = cursor.fetchall()
for row in rows:
    print(row)

cursor.close()
connection.close()