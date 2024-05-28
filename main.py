import sys
import asyncio
import time
import mysql.connector
from send_sms import send_sms
from telegram_bot import send_group_message
from auto_message import send_mail_to_new_customer
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from userInfo import username, password, username_netgsm, password_netgsm, login_url, order_page, user_page, index_page, db_host, db_username, db_password, db_database

# Check if we are in type checking mode
if sys.version_info >= (3, 5):
    from typing import TYPE_CHECKING
else:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from selenium.webdriver.remote.webelement import WebElement

class GetInfo:
    def __init__(self, is_order_info):
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("window-size=1024,768")
        self.chrome_options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.username = username
        self.password = password
        self.username_netgsm = username_netgsm
        self.password_netgsm = password_netgsm
        self.login_url = login_url
        self.order_page = order_page
        self.user_page = user_page
        self.index_page = index_page
        self.is_order_info = is_order_info
        self.max_retries = 5
        self.db_connection = mysql.connector.connect(
            host=db_host,
            user=db_username,
            password=db_password,
            database=db_database
        )
        self.db_cursor = self.db_connection.cursor()

    def log_in(self):
        retried = 0
    
        while retried < self.max_retries:
            try:
                t = time.localtime()
                t_str = time.strftime("%H:%M:%S", t)
                print(f"{t_str} - Trying To Login To Admin Panel")
                self.driver.get(self.login_url)

                username_input = WebDriverWait(self.driver, 40).until(
                    EC.presence_of_element_located((By.XPATH, "/html/body/div/div[2]/div/form/div/div[3]/input"))
                )
                password_input = WebDriverWait(self.driver, 40).until(
                    EC.presence_of_element_located((By.XPATH, "/html/body/div/div[2]/div/form/div/div[4]/input"))
                )
                login_button = WebDriverWait(self.driver, 40).until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/div/div[2]/div/form/div/button"))
                )
                username_input.send_keys(self.username)
                password_input.send_keys(self.password)
                login_button.click()

                retried = 0
                WebDriverWait(self.driver, 40).until(
                    EC.url_to_be(self.index_page)
                )

                if(self.is_order_info):
                    print(f"{t_str} - Checking Orders - Logged In Successfully")
                else:
                    print(f"{t_str} - Checking New Customers - Logged In Successfully")

                break
            except:
                retried += 1
                print(f"Login Retrying... Attempt {retried}/{self.max_retries}")
                time.sleep(1)

        if retried == self.max_retries:
            print("Max retries reached. Exiting.")
            sys.exit()    
    
    def get_to_page(self):
        retried = 0

        while retried < self.max_retries:
            try:
                t = time.localtime()
                t_str = time.strftime("%H:%M:%S", t)
                page_type = "Order" if self.is_order_info else "Customer"
                print(f"{t_str} - Trying to Get To {page_type} Page")
                page_url = order_page if self.is_order_info else user_page
                self.driver.get(page_url)

                table = WebDriverWait(self.driver, 40).until(
                    EC.presence_of_element_located((By.XPATH, "//*[@id='datatable-default']"))
                )

                if not self.is_order_info:
                    register_date = self.driver.find_element(By.XPATH, '//*[@id="datatable-default"]/thead/tr/th[6]')
                    register_date.click()
                    register_date.click()

                rows = WebDriverWait(self.driver, 40).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "tr"))
                )

                if (table and rows):
                    if(self.is_order_info):
                        print(f"{t_str} - Checking Orders - Found Tables and Rows Successfully")
                    else:
                        print(f"{t_str} - Checking New Customers - Found Tables and Rows Successfully")

                retried = 0

                return table, rows
            except Exception as e:
                retried += 1
                print(f"Getting to Page Retrying... Attempt {retried}/{self.max_retries}")
                time.sleep(1)
            
        if retried == self.max_retries:
            print("Max retries reached. Exiting.")
            sys.exit()

    async def check_rows(self):
        text = "Yeni Sipariş" if self.is_order_info else "Yeni Üye"
        t = time.localtime()
        t_str = time.strftime("%H:%M:%S", t)
        print(t_str + " - " + text + " Kontrol Başladı.")
        table, rows = self.get_to_page()
        
        column_indices_to_store = [0, 2, 3, 4, 5] if self.is_order_info else [0, 1, 2, 3, 4, 5]
        column_names = ["ID", "Üye Adı", "Sipariş Tutarı", "Mektup Adı", "Tarih", "Telefon Numarası", "Müşteri ID", "Postaya Verileceği Tarih"] if self.is_order_info else ["ID", "Ad Soyad", "Email", "Durum", "Üyelik Tipi", "Kayıt Tarihi"]
        
        if self.is_order_info:
            for i in range(1, len(rows)):
                # Getting Column Indices Informations
                columns = rows[i].find_elements(By.TAG_NAME, "td")
                row_data = [columns[j].text for j in column_indices_to_store]

                phone_number, isForeign, customer_id, transport_date = self.additional_infos(row_data[0])
                row_data.extend([phone_number, customer_id, transport_date])

                
                try:
                    insert_query = """INSERT INTO website_orders (order_id, customer_name, order_price, letter_name, order_date, 
                                    phone_number, customer_id, date_for_transport, track_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL)"""
                    self.db_cursor.execute(insert_query, tuple(row_data[:9]))
                    self.db_connection.commit()
                    print("Data inserted successfully")
                except mysql.connector.Error as err:
                    if err.errno == 1062:  # Duplicate entry error
                        print(f"{t_str} - Duplicate order entry. Skipping insertion.")
                        break
                    else:
                        print("Error inserting data:", err)

                if isForeign:
                    print(f"{t_str} - Yabancı Numara Tespit Edildi SMS İletilmedi. Numara: " + phone_number)
                else :
                    print(f"{t_str} - SMS Gönderimi Deneniyor. Numara: " + phone_number)
                    message_sms = "Değerli müşterimiz, Mektup Evi üzerinden vermiş olduğunuz siparişiniz onaylanmıştır. Siparişiniz teslimat durumuna geçtiği zaman takip bilgileri size iletilecektir. Bizi tercih ettiğiniz için teşekkür ederiz."
                    message_utf8 = message_sms.encode('utf-8')
                    send_sms(message_utf8, phone_number)

                message = f"<b>Yeni Sipariş Bilgisi:</b>\n" + "\n".join([f"<b>{column_names[j]}:</b> {row_data[j]}" for j in range(len(column_names))])
                send_group_message(message)

                print(row_data)
                table, rows = self.get_to_page()
        else:
            for i in range(1, len(rows)):
                columns = rows[i].find_elements(By.TAG_NAME, "td")
                row_data = [columns[i].text for i in column_indices_to_store]

                try:
                    insert_query = """INSERT INTO customer_list (customer_id, customer_name, email, status, privilage, 
                                    signup_date) VALUES (%s, %s, %s, %s, %s, %s)"""
                    self.db_cursor.execute(insert_query, tuple(row_data[:6]))
                    self.db_connection.commit()
                    print("Data inserted successfully")
                except mysql.connector.Error as err:
                    if err.errno == 1062:  # Duplicate entry error
                        print(f"{t_str} - Duplicate customer entry. Skipping insertion.")
                        break
                    else:
                        print("Error inserting data:", err)
                    
                try:
                    await send_mail_to_new_customer(row_data[2])
                    print(row_data[2] + " adresine mail gönderildi.")
                except Exception as e:
                    print("Mail Gönderimi Hatası: " + str(e))

                message = f"<b>Yeni Müşteri Bilgisi:</b>\n" + "\n".join([f"<b>{column_names[j]}:</b> {row_data[j]}" for j in range(len(column_names))])
                print(row_data)
                send_group_message(message)

    def additional_infos(self, order_id):
        retried = 0

        while retried < self.max_retries:
            try:
                isForeign = False
                self.driver.get(f"{self.order_page}/edit/{order_id}")

                go_to_customer_button = WebDriverWait(self.driver, 40).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="home"]/div[3]/a'))
                )

                letter_details = WebDriverWait(self.driver, 40).until(
                    EC.element_to_be_clickable((By.XPATH, '/html/body/section/div/section/div/div/form/div/ul/li[2]/a'))
                )
                letter_details.click()

                transport_date = WebDriverWait(self.driver, 40).until(
                    EC.presence_of_element_located((By.XPATH, '/html/body/section/div/section/div/div/form/div/div/div[2]/div[7]/div/p'))
                )
                transport_date = transport_date.text

                customer_link = go_to_customer_button.get_attribute("href")
                customer_link_split = customer_link.split("/")
                customer_id = customer_link_split[-1]
                # go_to_customer_button.click()
                self.driver.get(self.user_page + "/edit/" + customer_id)

                phone_number = WebDriverWait(self.driver, 40).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="telephone"]'))
                )
                phone_number = phone_number.get_attribute("value")
                    
                if phone_number.startswith("0"):
                    phone_number = phone_number[1:]
                elif phone_number.startswith("+90"):
                    phone_number = phone_number.replace("+90", "")
                elif phone_number.startswith("+"):
                    isForeign = True
                    phone_number = phone_number.replace("+", "00")
                phone_number = phone_number.replace(" ", "")
                phone_number = phone_number.replace("(", "")
                phone_number = phone_number.replace(")", "")
                phone_number = phone_number.replace("-", "")

                retried = 0
                return phone_number, isForeign, customer_id, transport_date
            except:
                retried += 1
                print(f"Trying to get additional infos... Attempt {retried}/{self.max_retries}")
                time.sleep(1)

        if retried == self.max_retries:
            print("Max retries reached. Exiting.")
            sys.exit()
    
    def log_out(self):
        profile_button = WebDriverWait(self.driver, 40).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/section/header/div[2]/div/a'))
        )
        profile_button.click()

        logout_button = WebDriverWait(self.driver, 40).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/section/header/div[2]/div/div/ul/li[4]/a'))
        )
        logout_button.click()

    def close(self):
        self.driver.quit()   

    async def run(self):
        self.log_in()
        while True:
            await self.check_rows()
            t = time.localtime()
            check_type = "Yeni Sipariş Kontrolü" if self.is_order_info else "Yeni Müşteri Kontrolü"
            print(time.strftime("%H:%M:%S", t) + " - " + check_type + " Tamamlandı Başa Dönülüyor. \n")
            
            current_time = time.localtime()
            if current_time.tm_hour == 0 and current_time.tm_min == 0:
                self.log_out()
                self.log_in()
            
            await asyncio.sleep(5)

if __name__ == "__main__":
    order_info = GetInfo(is_order_info=True)
    customer_info = GetInfo(is_order_info=False)

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(customer_info.run(), order_info.run()))
    except KeyboardInterrupt:
        print("Scanning stopped by user.")
    finally:
        order_info.close()
        customer_info.close()
        loop.close()
