"""
This code will mainly rely on the restaurant_id of each restaurant to get the restaurant details, menu and reviews of that restaurant.
The reason for this is because I hope to get data from as many restaurants as possible instead of relying on the area.
"""

import requests
import pandas as pd
import time
import os


def get_guest_token():
    res = requests.post(
        "https://gw.be.com.vn/api/v1/be-delivery-gateway/api/v1/user/guest", json={}
    )
    return res.json().get("access_token")


def fetch_restaurant_detail(restaurant_id, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Origin": "https://food.be.com.vn",
        "Referer": "https://food.be.com.vn",
        "User-Agent": "Mozilla/5.0",
    }

    payload = {
        "restaurant_id": restaurant_id,
        "latitude": 10.7769,  # location of Ho Chi Minh City
        "longitude": 106.7009,
        "merchant_category_id": 9,
        "page": 1,
        "limit": 50,
    }

    url = "https://gw.be.com.vn/api/v1/be-marketplace/web/restaurant/detail"
    resp = requests.post(url, json=payload, headers=headers)
    data = resp.json().get("data", {})

    restaurant_info_raw = data.get("restaurant_info", {})
    restaurant_info = {
        "restaurant_id": restaurant_info_raw.get("restaurant_id"),
        "restaurant_name": restaurant_info_raw.get("name"),
        "min_delivery_time": restaurant_info_raw.get("min_delivery_time"),
        "latitude": restaurant_info_raw.get("latitude"),
        "longitude": restaurant_info_raw.get("longitude"),
        "display_address": restaurant_info_raw.get("display_address"),
        "rating": restaurant_info_raw.get("rating"),
        "review_count": restaurant_info_raw.get("review_count"),
        "city": restaurant_info_raw.get("city"),
        "calling_number": restaurant_info_raw.get("calling_number"),
        "phone_no": restaurant_info_raw.get("phone_no"),
        "merchant_id": restaurant_info_raw.get("merchant_id"),
        "median_price": restaurant_info_raw.get("median_price"),
        "is_pickup_enable": restaurant_info_raw.get("is_pickup_enable"),
        "merchant_category_id": restaurant_info_raw.get("merchant_category_id"),
        "merchant_category_name": restaurant_info_raw.get("merchant_category_name"),
    }

    categories = data.get("categories", [])
    dish_list = []
    for cat in categories:
        category_id = cat.get("category_id")
        category_name = cat.get("category_name")
        items = cat.get("items", [])
        for item in items:
            dish_list.append(
                {
                    "restaurant_id": item.get("restaurant_id"),
                    "category_id": category_id,
                    "category_name": category_name,
                    "restaurant_item_id": item.get("restaurant_item_id"),
                    "item_name": item.get("item_name"),
                    "price": item.get("price"),
                    "old_price": item.get("old_price"),
                    "show_food_type": item.get("show_food_type"),
                    "order_count": item.get("order_count"),
                    "like_count": item.get("like_count"),
                    "is_veg": item.get("is_veg"),
                    "item_details": item.get("item_details"),
                }
            )

    return restaurant_info, dish_list


def fetch_reviews(restaurant_id, token):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    all_reviews = []
    page = 1
    per_page = 100

    while True:
        review_payload = {
            "restaurant_id": restaurant_id,
            "page": page,
            "limit": per_page,
            "locale": "vi",
            "client_info": {"locale": "vi", "device_type": 3},
        }

        url = "https://gw.be.com.vn/api/v1/be-merchant-gateway/web/customer/restaurant/ratings"
        resp = requests.post(url, json=review_payload, headers=headers)
        reviews_data = resp.json()

        page_reviews = reviews_data.get("ratings", [])
        if not page_reviews:
            break

        for r in page_reviews:
            rating_id = r.get("rating_id")

            all_reviews.append(
                {
                    "restaurant_id": restaurant_id,
                    "rating_id": rating_id,
                    "order_id": r.get("order_id"),
                    "user_name": r.get("user_name"),
                    "rating": r.get("rating"),
                    "feedback": r.get("feedback"),
                    "rated_at": r.get("rated_at"),
                    "merchant_feedback": r.get("merchant_feedback"),
                    "merchant_replied_at": r.get("merchant_replied_at"),
                    "dislike_items": r.get("dislike_items"),
                    "feedbacks": r.get("feedbacks"),
                }
            )
        page += 1
        time.sleep(0.5)

    return all_reviews


token = get_guest_token()

restaurant_ids = list(range(1, 20000))  # Change your restaurant_id range here

# Create directories
info_path = "befood/restaurants.csv"
dish_path = "befood/dishes.csv"
review_path = "befood/reviews.csv"

if not os.path.exists(info_path):
    pd.DataFrame(
        columns=["restaurant_id", "restaurant_name", "display_address"]
    ).to_csv(info_path, index=False)

if not os.path.exists(dish_path):
    pd.DataFrame(columns=["restaurant_id", "dish_name", "price"]).to_csv(
        dish_path, index=False
    )

if not os.path.exists(review_path):
    pd.DataFrame(columns=["restaurant_id", "user_name", "rating", "comment"]).to_csv(
        review_path, index=False
    )

for rid in restaurant_ids:
    try:
        print(f"Processing Restaurant with ID {rid}...")
        res_info, dishes = fetch_restaurant_detail(rid, token)
        reviews = fetch_reviews(rid, token)

        pd.DataFrame([res_info]).to_csv(info_path, mode="a", index=False, header=False)
        pd.DataFrame(dishes).to_csv(dish_path, mode="a", index=False, header=False)
        pd.DataFrame(reviews).to_csv(review_path, mode="a", index=False, header=False)

        print(
            f"[{rid}] Save {len(dishes)} dishes, {len(reviews)} reviews from: {res_info['restaurant_name']} – {res_info['display_address']}"
        )
        time.sleep(1)

    except Exception as e:
        print(f"Error at Restaurant with ID {rid}: {e}")
