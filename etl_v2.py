import requests 
from bs4 import BeautifulSoup 
import time
from urllib.parse import urljoin
import pandas as pd
import re
import sqlite3
import os

HTTP_TIMEOUT = 10
def extract():
    all_product = []
    url_avail = 'https://testingurl.dev'
    base_url = 'https://testingurl.dev/scraping/ecommerce'
    
    try:
        # 1. เพิ่ม timeout และ raise_for_status
        response = requests.get(base_url, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        category = ['laptops','phones' ,'headphones' ,'cameras']
        for page in category:
            url = f'https://testingurl.dev/scraping/ecommerce/category/{page}'  
            try:
                response_ = requests.get(url, timeout=HTTP_TIMEOUT)
                response_.raise_for_status()
                time.sleep(1)
                
                soup = BeautifulSoup(response_.text, 'html.parser')        
                products = soup.find_all('a', class_='card')
            
                for product in products:
                    product_name = product.find('h3')
                    product_title = product_name.text.strip() if product_name else None
                    
                    price = product.find('p')
                    price_ = price.contents[0].strip() if price else None

                    cate_ = page
                    
                    rating = product.find('span', class_='stars')
                    rating_ = rating.text.strip() if rating else None
                    
                    products_url = product.get('href') 
                    full_url = urljoin(url_avail, products_url)
                    
                    availability = None
                    if full_url:
                        respon = requests.get(full_url, timeout=HTTP_TIMEOUT)
                        respon.raise_for_status()
                        s = BeautifulSoup(respon.text, 'html.parser')       
                        avail = s.find('p', id="product-stock-display")
                        availability = avail.text.strip() if avail else None
                    
                    all_product.append({'product_name': product_title,
                                        'price': price_ ,
                                        'category': cate_ ,
                                        'rating': rating_ ,
                                        'availability': availability,
                                        'product_url': full_url})  
            except requests.RequestException as e:
                # ดักจับ Error ระหว่างดึงข้อมูลแต่ละ Category
                raise requests.RequestException(
                    f'Failed to extract category "{page}": {e}'
                )
    except requests.RequestException as e:
        # ดักจับ Error ระหว่างเข้าหน้า Base URL
        raise requests.RequestException(f'HTTP Request Error during extraction: {e}')

    return all_product

def transform(all_product):
    if not all_product:
        raise ValueError('ไม่พบข้อมูลที่ดึงมาได้ (all_product เป็นค่าว่าง)')
    
    df = pd.DataFrame(all_product)
    # price 
    df['price'] = df['price'].str.extract(r'(\d+\.\d+)').astype(float)
    df['price'] = df['price'].round(2)
    # rating
    rating_map= {
        "★☆☆☆☆": 1,
        "★★☆☆☆": 2,
        "★★★☆☆": 3,
        "★★★★☆": 4,
        "★★★★★": 5
    }
    df['rating'] = df['rating'].map(rating_map)
    # availability
    df['availability'] = df['availability'].str.replace(r"^\d+\s*", "", regex=True).str.strip()
    
    # Data Validation
    # 1. เช็คข้อมูลสำคัญที่เป็นค่าว่าง (Null/NaN)
    required_cols = ['product_name', 'price', 'product_url']
    missing_mask = df[required_cols].isna().any(axis=1)
    missing_count = missing_mask.sum()

    if missing_count > 0:
        invalid_rows = df[missing_mask][required_cols]
        raise ValueError(
            f'พบข้อมูลสำคัญ (product_name, price, product_url) เป็นค่าว่าง'
            f' {missing_count} รายการ!\nรายการที่มีปัญหา:\n{invalid_rows}'
        )

    # 2. เช็ค URL ซ้ำ
    duplicate_count = df.duplicated(subset=['product_url']).sum()
    if duplicate_count > 0:
        duplicate_rows = df[df.duplicated(subset=['product_url'], keep=False)][
            ['product_name', 'product_url']
        ]
        raise ValueError(
            f'พบ product_url ซ้ำกัน {duplicate_count} รายการ!\n'
            f'รายการที่ซ้ำกัน:\n{duplicate_rows}'
        )

    print('Data Validation ผ่านเรียบร้อย (ไม่มีค่าว่างสำคัญ และไม่มี URL ซ้ำ)')
    return df

def load(df):
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)

    csv_path = os.path.join(output_dir, 'products.csv')
    db_path = os.path.join(output_dir, 'products.db')
    table_name = 'products'

    conn = None
    db_records = 0
    try:
        conn = sqlite3.connect(db_path)
        df.to_sql('products', conn, if_exists='replace', index=False)
        
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM products")
        db_records = cursor.fetchone()[0]
        
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    except sqlite3.Error as e:
        raise RuntimeError(f'ล้มเหลวในการบันทึก SQLite: {e}')
    except Exception as e:
        raise RuntimeError(f'ล้มเหลวในการส่งออกไฟล์ CSV: {e}')
    finally:
        if conn:
            conn.close()
      
    print('\n==================================')
    print('       EXECUTION REPORT           ')
    print('==================================')
    print(f'Products extracted: {len(df)}')
    print(f'CSV export: PASS -> {csv_path}')
    print(f'SQLite export: PASS -> {db_path}')
    print(f'Database records: {db_records}')
    print('==================================')
    
if __name__ == '__main__':
    try:
        print('กำลังเริ่มรัน ETL Pipeline...')
        all_product = extract()
        df = transform(all_product)
        load(df)
        print('\nกระบวนการ ETL เสร็จสมบูรณ์แล้ว!')
    except Exception as e:
        print('\n [PIPELINE FAILED] กระบวนการถูกยกเลิกเนื่องจากเกิด Error:')
        print(f'สาเหตุ: {e}')