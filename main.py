#!/usr/bin/python
# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from pandas import DataFrame


# задаём список из ссылок для парсинга
TARGET_LIST = ["https://goldapple.ru/parfjumerija/zhenskie-aromaty-parfume", "https://goldapple.ru/makijazh/guby/gubnaja-pomada"]

# параметры для запуска вебдрайвера без открытия хрома
op = webdriver.ChromeOptions()
op.add_argument('headless')
driver = webdriver.Chrome(executable_path="chromedriver.exe", options=op)


# получаем хлебные крошки из карточки товара
def get_breadcrumbs():
    try:
        breadcrumbs = driver.find_elements_by_css_selector("span[class='paragraph-2 pdp-breadcrumbs__crumb']")
        breadcrumbs_units = []
        for i in breadcrumbs:
            breadcrumbs_units.append(i.get_attribute("textContent").strip())
        result = '/'.join(breadcrumbs_units)
    except NoSuchElementException:
        result = 'не найден'
    return result


# получаем бренд и название товара из карточки
def brand_name():
    try:
        brand = driver.find_element_by_css_selector("a[class='link-alt pdp-title__brand']").text
        name = driver.find_element_by_css_selector("span[class='pdp-title__name']").text
        brand_and_name = brand + " " + name.lower()
    except NoSuchElementException:
        brand_and_name = 'не найден'
    return brand_and_name


# получаем первую картинку товара из карточки
def get_image():
    try:
        img = driver.find_element_by_css_selector("img[class='product-gallery-placeholder__slide-image']").get_attribute("src")
    except NoSuchElementException:
        img = 'не найден'
    return img


# получаем артикул товара из карточки
def get_vendor_code():
    try:
        vendor_code = driver.find_element_by_css_selector("span[itemprop='sku']").get_attribute("textContent")
    except NoSuchElementException:
        vendor_code = 'не найден'
    return vendor_code


# получаем цену из карточки товара
def get_price():
    try:
        price = driver.find_element_by_xpath("//span[@data-price-type='finalPrice']/span").get_attribute("textContent")
    except NoSuchElementException:
        price = 'не найден'
    return price


# получаем оффер под ценой из карточки товара
def get_offer():
    try:
        offer = driver.find_element_by_css_selector("span[class='price-container price-final_price tax weee']").get_attribute("data-price-description")
        if offer is None:
            offer = ' '
    except NoSuchElementException:
        offer = 'не найден'
    return offer


# получаем описание из карточки товара
def get_description():
    try:
        description = driver.find_element_by_css_selector("section[class='product-description__description ']").get_attribute("textContent")
        description_res = ' '.join(description.split())
    except NoSuchElementException:
        description_res = 'не найден'
    return description_res


def main(target_urls_list):
    res_urls = []
    # сохраняем ссылки на карточки товаров с первых страниц из изначального списка
    for target_url in target_urls_list:
        driver.get(target_url)
        urls_units_start = driver.find_elements_by_css_selector("a[class='product photo']")
        for url in urls_units_start:
            res_urls.append(url.get_attribute("href"))
        # собираем ссылки на карточки товаров с учётом пагинации стартовых страниц
        urls_count = 1
        while True:
            try:
                urls_count += 1
                next_url = target_url + f"?p={urls_count}"
                driver.get(next_url)
                urls_units_next = driver.find_elements_by_css_selector("a[class='product photo']")
                for url in urls_units_next:
                    res_urls.append(url.get_attribute("href"))
                if urls_count == 5:
                    break
            except Exception as e:
                print(e)
    # парсим карточки товара
    res_all_urls = []
    res_images = []
    res_breadcrumbs = []
    res_brand_and_names = []
    res_vendor_codes = []
    res_prices = []
    res_offers = []
    res_descriptions = []
    for end_url in res_urls:
        driver.get(end_url)
        try:
            # если в элементе есть переключатель объёма, то парсим с учётом переключения
            difficult_product_div = driver.find_element_by_css_selector("div[class='swatch-field-wrapper swatch-field-radio']")
            all_buttons = driver.find_elements_by_xpath("//div[@class='radio-field__inner']/button")
            for button in all_buttons:
                if button.text != '':
                    driver.execute_script("arguments[0].click();", button)
                    res_all_urls.append(driver.current_url)
                    res_breadcrumbs.append(get_breadcrumbs())
                    res_brand_and_names.append(brand_name())
                    res_images.append(get_image())
                    res_vendor_codes.append(get_vendor_code())
                    res_prices.append(get_price())
                    res_offers.append(get_offer())
                    res_descriptions.append(get_description())
        except NoSuchElementException:
            # парсим карточку, если нет переключателя
            res_all_urls.append(driver.current_url)
            res_breadcrumbs.append(get_breadcrumbs())
            res_brand_and_names.append(brand_name())
            res_images.append(get_image())
            res_vendor_codes.append(get_vendor_code())
            res_prices.append(get_price())
            res_offers.append(get_offer())
            res_descriptions.append(get_description())
    # добавляем найденные значения в словарь
    result_dict = {
        "Ссылка на товар": res_all_urls,
        "Ссылка на картинку": res_images,
        "Хлебные крошки": res_breadcrumbs,
        "Название": res_brand_and_names,
        "Артикул": res_vendor_codes,
        "Цена": res_prices,
        "Оффер для цены": res_offers,
        "Описание": res_descriptions,
    }
    # записываем итоговые значения в файл csv с необходимыми параметрами и чистим список от строк без параметров
    data = DataFrame(result_dict)
    data = data.drop(data[(data['Ссылка на картинку'] == 'не найден') | (data['Хлебные крошки'] == 'не найден') | (data['Название'] == 'не найден') | (data['Артикул'] == 'не найден') | (data['Цена'] == 'не найден') | (data['Оффер для цены'] == 'не найден') | (data['Описание'] == 'не найден')].index)
    data.to_csv("res_task.csv", encoding='utf-8', index=False, sep='\t')


if __name__ == '__main__':
    main(TARGET_LIST)
