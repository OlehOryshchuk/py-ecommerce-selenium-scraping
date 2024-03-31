import csv
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

from dataclasses import dataclass, astuple
from urllib.parse import urljoin


BASE_URL = "https://webscraper.io/"

webscraper_page_urls = {
    "home": urljoin(BASE_URL, "test-sites/e-commerce/more/"),
    "computers": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/"),
    "phones": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/"),
    "laptops": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops/"),
    "tablets": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets/"),
    "touch": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch/"),
}

@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field for field in astuple(Product)]

# Product CSS selectors to which we are going to navigate
TITLE = ".caption > h4 > a"
DESCRIPTION = ".caption > .card-text"
PRICE = ".caption > .price"
RATING = ".ratings > p[data-rating]"
NUM_OF_REVIEWS = ".ratings > .review-count"

PRODUCTS_CARD = ".card_body"
PAGINATION_BUTTON = ".ecomerce-items-scroll-more"


class CVSFileManager:
    def __init__(self, file_name: str, column_fields: [str]):
        self.file_name = file_name
        self.column_fields = column_fields

    def write_in_cvs_file(self, data: list) -> None:
        with open(self.file_name, "w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(self.column_fields)
            writer.writerows([astuple(record) for record in data])


class WebDriverSingleton:
    _instance = None

    def __init__(self):
        if WebDriverSingleton._instance is not None:
            raise Exception("This class is singleton")
        WebDriverSingleton._instance = webdriver.Chrome()

    @staticmethod
    def get_driver() -> webdriver.Chrome:
        if WebDriverSingleton._instance is None:
            WebDriverSingleton()
        return WebDriverSingleton._instance


class ProductParser:
    """ Class for Parsing web app webscraper.io"""
    def __init__(self, page_url: str):
        self.page_url = urljoin(BASE_URL, page_url)
        self.page_soup = self.initiate_soup()

    def get_selenium_page(self) -> webdriver.Chrome:
        """ Get webdriver and GET page using self.page_url """
        driver = WebDriverSingleton.get_driver()
        driver.get(self.page_url)
        return driver

    def initiate_soup(self) -> BeautifulSoup:
        """ Return BeautifulSoup page"""
        page = requests.get(self.page_url).content
        return BeautifulSoup(page, "html.parser")

    @staticmethod
    def create_product(product_body: BeautifulSoup) -> Product:
        return Product(
            title=product_body.select_one(TITLE)["title"],
            description=product_body.select_one(DESCRIPTION).string,
            price=float(product_body.select_one(PRICE).string.replace("$", "")),
            rating=int(product_body.select_one(RATING)["data-rating"]),
            num_of_reviews=int(
                product_body.select_one(NUM_OF_REVIEWS).string.split(" ")[0]
            )
        )

    def has_pagination(self) -> bool:
        return bool(self.page_soup.select_one(PAGINATION_BUTTON))

    def more_products(self) -> None:
        """ Update the self.page_soup with more products from pagination """
        # check if page has pagination
        if self.has_pagination:
            driver = self.get_selenium_page()

            while self.has_pagination():
                # click pagination button
                more_products = driver.find_element(By.LINK_TEXT, "More")
                more_products.click()
            self.page_soup = BeautifulSoup(driver.page_source, "html.parser")

    def get_all_products(self) -> list[Product]:
        """ Return page products """
        self.more_products()
        products_soup = self.page_soup.select(PRODUCTS_CARD)
        return [self.create_product(product) for product in products_soup]


def get_all_products() -> None:
    # for file_name, url in webscraper_page_urls.items():
    #     products = ProductParser(page_url=url).get_all_products()
    #     file_manager = CVSFileManager(file_name=file_name, column_fields=PRODUCT_FIELDS)
    #     file_manager.write_in_cvs_file(data=products)
    file_name = webscraper_page_urls["home"]
    products = ProductParser(page_url=file_name).get_all_products()
    file_manager = CVSFileManager(file_name=file_name, column_fields=PRODUCT_FIELDS)
    file_manager.write_in_cvs_file(data=products)

if __name__ == "__main__":
    get_all_products()
