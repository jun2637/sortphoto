import os
import shutil
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut


SOURCE_FOLDER = r'C:\Users\parkjj\Desktop\wonbon'  # 정리할 사진들이 있는 원본 폴더 경로
DEST_FOLDER = r'C:\Users\parkjj\Desktop\new' # 지역별로 분류된 사진이 저장될 새 폴더 경로


geolocator = Nominatim(user_agent="photosort")

def get_exif_data(image_path):
    try:
        image = Image.open(image_path)
        image.verify() 
        image = Image.open(image_path)
        info = image._getexif()
        if not info:
            return None
        
        exif_data = {}
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_data = {}
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_data[sub_decoded] = value[t]
                exif_data[decoded] = gps_data
            else:
                exif_data[decoded] = value
        return exif_data
    except Exception as e:
        return None

def convert_to_degrees(value):
    d = float(value[0])
    m = float(value[1])
    s = float(value[2])
    return d + (m / 60.0) + (s / 3600.0)

def get_lat_lon(exif_data):
    if not exif_data or "GPSInfo" not in exif_data:
        return None, None

    gps_info = exif_data["GPSInfo"]
    gps_latitude = gps_info.get("GPSLatitude")
    gps_latitude_ref = gps_info.get("GPSLatitudeRef")
    gps_longitude = gps_info.get("GPSLongitude")
    gps_longitude_ref = gps_info.get("GPSLongitudeRef")

    if not all([gps_latitude, gps_latitude_ref, gps_longitude, gps_longitude_ref]):
        return None, None

    lat = convert_to_degrees(gps_latitude)
    if gps_latitude_ref != "N":
        lat = -lat

    lon = convert_to_degrees(gps_longitude)
    if gps_longitude_ref != "E":
        lon = -lon

    return lat, lon

def get_location_name(lat, lon):
    try:
        location = geolocator.reverse((lat, lon), language='ko')
        if location and location.raw.get('address'):
            address = location.raw['address']
            city = address.get('city', address.get('town', address.get('province', '알수없는_지역')))
            return city
    except GeocoderTimedOut:
        return "시간_초과_지역"
    except Exception:
        return "알수없는_지역"
    return "알수없는_지역"

def organize_photos():
    if not os.path.exists(DEST_FOLDER):
        os.makedirs(DEST_FOLDER)

    for filename in os.listdir(SOURCE_FOLDER):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
            file_path = os.path.join(SOURCE_FOLDER, filename)
            
            exif_data = get_exif_data(file_path)
            lat, lon = get_lat_lon(exif_data)

            if lat and lon:
                location_name = get_location_name(lat, lon)
            else:
                location_name = "GPS_정보_없음"

            target_folder = os.path.join(DEST_FOLDER, location_name)
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)

            target_path = os.path.join(target_folder, filename)
            shutil.copy2(file_path, target_path)
            print(f"[{location_name}] 폴더로 복사 완료: {filename}")

if __name__ == "__main__":
    organize_photos()
    print("사진 분류 작업이 모두 완료되었습니다.")
