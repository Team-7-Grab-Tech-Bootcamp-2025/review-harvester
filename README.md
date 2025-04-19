# review-harvester
A multi-source food review crawler that collects *customer feedback* and *restaurant details* (location, rating, menu, operation time) from *BeFood, ShopeeFoodFood (shopeefood), and Google*. Designed for unified data aggregation, cross-platform sentiment analysis, and scheduled automation to keep your datasets continuously updated. The collected data will also serve downstream applications such as training AI models to classify feedback into 5 categories and powering a food recommendation chatbot that suggests dishes based on user preferences (e.g., soup like 'Bún', 'Phở'), nearby location, or popularity.

This project also includes scripts to assist in discovering API from different platforms through browser inspection sources. All you need to do is copy the browser sources into a .txt file and let me know where the file is located. I will then return the API data extracted from it.

This repository only includes a small sample of the full dataset to give you a better idea of what the data will look like after running the code.

## Features
 1. Crawl customer reviews with rating, content, and timestamps.

 2. Extract restaurant metadata: name, address, rating, location (lat/lon), menu.

 3. Collect structured menu and dish data per restaurant (ShopeeFood, BeFood).

 4. Scheduled automation supported.

 5. Save results to structured CSV or Excel files for downstream analytics and training models.

## Project Structure

```
review-harvester/
├── shopeefood/        
    ├── restaurants.csv
    ├── reviews.csv
    ├── dishes.csv (menu of restaurant)
├── befood/     
    ├── restaurants.csv
    ├── ...
    ├── ...       
├── googlemaps/   
    ├── restaurants.csv
    ├── reviews.csv
├── get_apis.py             
├── befood_crawl.py   
├── shopeefood_crawl.py               
├── requirements.txt           
└── README.md                  
```
## How to Run
### 1. Install dependencies
```
pip install -r requirements.txt
```
### 2. Run Befood/shopeefood crawler script
You need to access `shopeefood_crawl.py` or `befood_crawl.py` file, in User_Agent path, you need to fill your valid string. 
#### Befood
``` 
python befood_crawl.py
```
#### shopeefood (Shopee)
```
python shopeefood_crawl.py
```
### 3. Scheduled Automation 

## Author
Developed by **Hoa Dam Nguyen Quynh** – an AI Engineer participating in the Grab's BootCamp program. 
If you want to contribute, suggest or collaborate, please contact me via email `damnguyenquynhhoa@gmail.com`.
