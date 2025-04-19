"""
This code will mainly locate restaurants in a certain area to get restaurant information, get restaurant_id
to find reviews and menu of that restaurant.
"""

import requests
import time
import pandas as pd
from tqdm import tqdm
import os

# Config
HEADERS = {
    ### You need to fill in a valid User-Agent, find it in your browser's dev tools (Network -> Headers)
    "User-Agent": "Mozilla/5.0 ... ",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.foody.vn/ho-chi-minh",
    "Origin": "https://www.foody.vn",
    "X-Foody-App-Type": "1004",
    "X-Foody-Api-Version": "1",
    "X-Foody-Client-Type": "1",
    "X-Foody-Client-Version": "1",
    "X-Foody-Client-Id": "",
    "X-Foody-Client-Language": "vi",
    "X-Requested-With": "XMLHttpRequest",
}

# Output files path
RESTAURANT_CSV = "shopeefood/restaurants.csv"
DISHES_CSV = "shopeefood/dishes.csv"
REVIEWS_CSV = "shopeefood/reviews.csv"


# convert K/M to number
def parse_review_count(text):
    if not text:
        return 0
    try:
        text = str(text).strip().upper()
        if "K" in text:
            return int(float(text.replace("K", "")) * 1000)
        elif "M" in text:
            return int(float(text.replace("M", "")) * 1_000_000)
        elif "B" in text:
            return int(float(text.replace("B", "")) * 1_000_000_000)
        return int(text)
    except:
        return 0


# Fetch data functions
def fetch_restaurants(lat=10.762622, lon=106.660172, per_page=30, max_pages=3):
    restaurant_list = []
    for page in range(1, max_pages + 1):
        url = "https://www.foody.vn/__get/Place/HomeListPlace"
        params = {
            "t": int(time.time() * 1000),
            "page": page,
            "lat": lat,
            "lon": lon,
            "count": per_page,
            "districtId": "",
            "cateId": "",
            "cuisineId": "",
            "isReputation": "",
            "type": 1,
        }
        try:
            res = requests.get(url, params=params, headers=HEADERS)
            data = res.json()
            # print (data)  #Uncomment this line if you want to see the raw data and re-choose the keys

            items = data.get("Items", [])
            if not items:
                break
            restaurant_list.extend(items)
            time.sleep(0.3)
        except Exception as e:
            print(f"Error on page {page}: {e}")
            break
    return restaurant_list


def fetch_dishes(restaurant_id):
    url = "https://gappapi.deliverynow.vn/api/dish/get_delivery_dishes"
    params = {"request_id": restaurant_id, "id_type": 1}
    try:
        res = requests.get(url, headers=HEADERS, params=params)
        data = res.json()
        # print (data)  #Uncomment this line if you want to see the raw data and re-choose the keys
        dish_data = []
        for group in data.get("reply", {}).get("menu_infos", []):
            for dish in group.get("dishes", []):
                dish_data.append(
                    {
                        "restaurant_id": restaurant_id,
                        "dish_type_id": group.get("dish_type_id"),
                        "dish_type_name": group.get("dish_type_name"),
                        "dish_id": dish.get("id"),
                        "dish_name": dish.get("name"),
                        "description": dish.get("description"),
                        "price": dish.get("price", {}).get("value"),
                        "is_active": dish.get("is_active"),
                        "is_available": dish.get("is_available"),
                        "is_group_discount_item": dish.get("is_group_discount_item"),
                        "total_like": dish.get("total_like"),
                    }
                )
        return dish_data
    except Exception as e:
        print(f" Error fetching dishes for {restaurant_id}: {e}")
        return []


def convert_raw_review_to_structured(item):
    return {
        "review_id": item.get("Id"),
        "user_id": item.get("Owner", {}).get("Id"),
        "user_name": item.get("Owner", {}).get("DisplayName"),
        "user_level": item.get("Owner", {}).get("Level"),
        "title": item.get("Title"),
        "review_text": item.get("Description"),
        "rating": item.get("AvgRating"),
        "created_date": item.get("CreatedOnTimeDiff"),
        "device": item.get("DeviceName"),
        "restaurant_id": item.get("ResId"),
        "total_views": item.get("TotalViews"),
        "total_likes": item.get("TotalLike"),
        "total_comments": item.get("TotalComment"),
        "review_url": "https://www.foody.vn" + item.get("Url", ""),
    }


def fetch_reviews(res_id):
    reviews = []
    last_id = ""
    while True:
        url = f"https://www.foody.vn/__get/Review/ResLoadMore?ResId={res_id}&LastId={last_id}&Count=10&Type=1&isLatest=true&ExcludeIds="
        try:
            r = requests.get(url, headers=HEADERS)
            data = r.json()
            # print (data)  #Uncomment this line if you want to see the raw data and re-choose the keys
        except Exception as e:
            print(f"Error fetching reviews for {res_id}: {e}")
            break

        items = data.get("Items", [])
        if not items:
            break

        for item in items:
            reviews.append(convert_raw_review_to_structured(item))

        last_id = items[-1].get("Id")
        time.sleep(1)
    return reviews


# Main pipeline
def build_and_save_to_csv(max_pages=1000):
    restaurants = fetch_restaurants(max_pages=max_pages)

    for item in tqdm(restaurants, desc="Processing restaurants"):
        rid = item.get("Id")

        # restaurant info
        rest_row = {
            "restaurant_id": rid,
            "restaurant_name": item.get("Name"),
            "min_delivery_time": 30,
            "latitude": item.get("Latitude"),
            "longitude": item.get("Longitude"),
            "display_address": item.get("Address"),
            "rating": float(item.get("AvgRatingText") or 0),
            "review_count": parse_review_count(item.get("TotalReviewsFormat")),
            "is_pickup_enable": False,
        }
        pd.DataFrame([rest_row]).to_csv(
            RESTAURANT_CSV,
            mode="a",
            header=not os.path.exists(RESTAURANT_CSV),
            index=False,
        )

        # dishes
        d = fetch_dishes(rid)
        if d:
            pd.DataFrame(d).to_csv(
                DISHES_CSV, mode="a", header=not os.path.exists(DISHES_CSV), index=False
            )
        else:
            print(f"Restaurant ID : {rid} No dishes found")

        # reviews
        r = fetch_reviews(rid)
        if r:
            pd.DataFrame(r).to_csv(
                REVIEWS_CSV,
                mode="a",
                header=not os.path.exists(REVIEWS_CSV),
                index=False,
            )

        time.sleep(0.2)


if __name__ == "__main__":
    # Change this to the number of pages you want to crawl
    build_and_save_to_csv(max_pages=1000)
    print("Crawling completed and saved to CSV files.")
