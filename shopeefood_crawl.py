import requests
import time
import pandas as pd
import os
from tqdm.auto import tqdm
from bs4 import BeautifulSoup

# --------------------
# Config
# --------------------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
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


RESTAURANT_CSV = "shopeefood_3/restaurants.csv"
DISHES_CSV = "shopeefood_3/dishes.csv"
REVIEWS_CSV = "shopeefood_3/reviews.csv"


# Crawl Review API
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


def get_reviews_from_foody(res_id):
    reviews = []
    last_id = ""
    while True:
        url = f"https://www.foody.vn/__get/Review/ResLoadMore?ResId={res_id}&LastId={last_id}&Count=10&Type=1&isLatest=true&ExcludeIds="
        try:
            r = requests.get(url, headers=HEADERS)
            data = r.json()
        except Exception as e:
            tqdm.write(f"Error fetching reviews for {res_id}: {e}")
            break

        items = data.get("Items", [])
        if not items:
            break

        for item in items:
            reviews.append(convert_raw_review_to_structured(item))

        last_id = items[-1].get("Id")
        time.sleep(1)
    return reviews


# --------------------
# Crawl Menu API
# --------------------
def fetch_dishes(restaurant_id):
    url = f"https://gappapi.deliverynow.vn/api/dish/get_delivery_dishes?request_id={restaurant_id}&id_type=1"
    try:
        res = requests.get(url, headers=HEADERS)
        data = res.json()
        dish_data = []
        for category in data["reply"]["menu_infos"]:
            dish_type_id = category.get("dish_type_id")
            dish_type_name = category.get("dish_type_name")

            for dish in category.get("dishes", []):
                dish_data.append(
                    {
                        "dish_type_id": dish_type_id,
                        "dish_type_name": dish_type_name,
                        "id": dish.get("id"),
                        "name": dish.get("name"),
                        "price": dish.get("price", {}).get("value"),
                        "is_active": dish.get("is_active"),
                        "total_like": dish.get("total_like"),
                        "is_available": dish.get("is_available"),
                        "is_group_discount_item": dish.get("is_group_discount_item"),
                        "description": dish.get("description"),
                    }
                )

        return dish_data
    except Exception as e:
        tqdm.write(f"Error fetching dishes for {restaurant_id}: {e}")
        return []


# --------------------
# Crawl HTML từ Foody.vn
# --------------------
def get_restaurant_info_from_foody(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            tqdm.write(f"Không thể truy cập trang: {url}")
            return {}

        soup = BeautifulSoup(resp.content, "html.parser")
        name_tag = soup.find("h1")
        restaurant_name = name_tag.text.strip() if name_tag else None

        address_tag = soup.find("span", itemprop="streetAddress")
        if address_tag:
            district_tag = soup.find("span", itemprop="addressLocality")
            city_tag = soup.find("span", itemprop="addressRegion")
            address = f"{address_tag.text.strip()}, {district_tag.text.strip() if district_tag else ''}, {city_tag.text.strip() if city_tag else ''}"
        else:
            address = None

        rating_tag = soup.find("div", itemprop="ratingValue")
        review_count_tag = soup.find("div", itemprop="reviewCount")
        rating = rating_tag.text.strip() if rating_tag else None
        review_count = review_count_tag.text.strip() if review_count_tag else None

        lat_tag = soup.find("meta", {"itemprop": "latitude"})
        long_tag = soup.find("meta", {"itemprop": "longitude"})
        latitude = lat_tag.get("content") if lat_tag else None
        longitude = long_tag.get("content") if long_tag else None

        cuisine_tags = soup.find_all("a", class_="microsite-cuisine")
        cuisines = [c.text.strip().rstrip(",") for c in cuisine_tags]

        return {
            "restaurant_name": restaurant_name,
            "address": address,
            "rating": rating,
            "review_count": review_count,
            "latitude": latitude,
            "longitude": longitude,
            "categories": cuisines,
            "url": url,
        }
    except Exception as e:
        tqdm.write(e)
        return {}


# --------------------
# Main runner
# --------------------
def process_restaurant_by_id(rid):
    reviews = get_reviews_from_foody(rid)
    if not reviews:
        tqdm.write(f"Restaurant with ID : {rid} have no review")
        return

    pd.DataFrame(reviews).to_csv(
        REVIEWS_CSV, mode="a", header=not os.path.exists(REVIEWS_CSV), index=False
    )

    review_url = reviews[0].get("review_url")
    rest_url = "/".join(review_url.split("/")[:-1]) if review_url else None

    if rest_url:
        info = get_restaurant_info_from_foody(rest_url)
        df = pd.DataFrame(
            [
                {
                    "restaurant_id": rid,
                    "restaurant_name": info.get("restaurant_name"),
                    "address": info.get("address"),
                    "rating": info.get("rating"),
                    "review_count": info.get("review_count"),
                    "latitude": info.get("latitude"),
                    "longitude": info.get("longitude"),
                    "categories": ", ".join(info.get("categories", [])),
                    "url": info.get("url"),
                }
            ]
        )
        df.to_csv(
            RESTAURANT_CSV,
            mode="a",
            header=not os.path.exists(RESTAURANT_CSV),
            index=False,
        )

    if rid:
        dishes = fetch_dishes(rid)
        if not dishes:
            tqdm.write(f"Không lấy được menu từ Restaurant ID {rid}")
        if dishes:
            pd.DataFrame(dishes).to_csv(
                DISHES_CSV, mode="a", header=not os.path.exists(DISHES_CSV), index=False
            )


# --------------------
# Start
# --------------------
def run_pipeline_by_id_range(start_id=1, end_id=10):
    for rid in tqdm(range(start_id, end_id + 1), desc="Scanning Foody ID"):
        try:
            process_restaurant_by_id(rid)
            time.sleep(0.3)
        except Exception as e:
            tqdm.write(f"Restaurant ID {rid} lỗi: {e}")


if __name__ == "__main__":
    run_pipeline_by_id_range(1, 1000000)
    tqdm.write("Crawl completed.")
