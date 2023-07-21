import os
import csv
from datetime import date
from bs4 import BeautifulSoup
import requests
import concurrent.futures

class AmazonProductScraper:
    def __init__(self):
        self.category_name = None
        self.formatted_category_name = None
        self.max_pages = 100  # Maximum number of pages to scrape

    def fetch_webpage_content(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        return response.text

    def get_category_url(self):
        self.category_name = input("\n>> Enter the product/category to be searched: ")
        self.formatted_category_name = self.category_name.replace(" ", "+")
        category_url = f"https://www.amazon.in/s?k={self.formatted_category_name}&ref=nb_sb_noss"
        print(">> Category URL: ", category_url)
        return category_url

    @staticmethod
    def extract_product_information(page_results):
        temp_record = []
        for item in page_results:
            description = item.h2.a.text.strip()
            category_url = "https://www.amazon.in/" + item.h2.a.get('href')

            try:
                product_price = item.find('span', 'a-offscreen').text
            except AttributeError:
                product_price = "N/A"

            try:
                product_review = item.i.text.strip()
            except AttributeError:
                product_review = "N/A"

            try:
                review_number = item.find('span', {'class': 'a-size-base'}).text
            except AttributeError:
                review_number = "N/A"

            product_information = (description, product_price[1:], product_review, review_number, category_url)
            temp_record.append(product_information)

        return temp_record

    def process_page(self, page_number, category_url):
        print(f">> Page {page_number} - webpage information extracted")
        next_page_url = category_url + f"&page={page_number}"
        page_content = self.fetch_webpage_content(next_page_url)
        soup = BeautifulSoup(page_content, 'html.parser')
        page_results = soup.find_all('div', {'data-component-type': 's-search-result'})
        return self.extract_product_information(page_results)

    def navigate_to_other_pages(self, category_url):
        records = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_page = {executor.submit(self.process_page, page_number, category_url): page_number for page_number in range(2, self.max_pages + 1)}
            for future in concurrent.futures.as_completed(future_to_page):
                page_number = future_to_page[future]
                try:
                    temp_record = future.result()
                    records += temp_record
                except Exception as e:
                    print(f"Exception occurred for page {page_number}: {e}")

        print("\n>> Creating an excel sheet and entering the details...")
        return records

    def product_information_spreadsheet(self, records):
        today = date.today().strftime("%d-%m-%Y")
        file_name = f"{self.category_name}_{today}.csv"

        with open(file_name, "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Description', 'Price', 'Rating', 'Review Count', 'Product URL'])
            writer.writerows(records)

        message = f">> Information about the product '{self.category_name}' is stored in {file_name}\n"
        print(message)
        os.startfile(file_name)


if __name__ == "__main__":
    my_amazon_bot = AmazonProductScraper()

    category_details = my_amazon_bot.get_category_url()

    navigation = my_amazon_bot.navigate_to_other_pages(category_details)

    my_amazon_bot.product_information_spreadsheet(navigation)
