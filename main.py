# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
import unittest
import time
import json
import requests


class KolesaKz(unittest.TestCase):
    IMAGE_PATH = u"/home/ysklyarov/"
    CAPTCHA_SIZE = 40
    CLIENT_ID = ""

    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(1000)
        self.base_url = "https://www.kolesa.kz/"
        self.verificationErrors = []
        self.accept_next_alert = True

    def fill_fields(self):
        driver = self.driver
        Select(driver.find_element_by_id("change-section-select")).select_by_visible_text(u"Запчасти")
        driver.find_element_by_css_selector("option[value=\"2\"]").click()
        time.sleep(2)
        driver.find_element_by_css_selector("option[value=\"spare.parts\"]").click()
        time.sleep(4)
        Select(driver.find_element_by_id("auto-car-mm-0")).select_by_visible_text("BMW")
        driver.find_element_by_css_selector("option[value=\"11\"]").click()
        time.sleep(2)
        #Select(driver.find_element_by_id("auto-car-mm-1")).select_by_visible_text("   118")
        driver.find_element_by_css_selector("#auto-car-mm-1 > option[value=\"3\"]").click()
        time.sleep(3)
        #Select(driver.find_element_by_id("auto-generation")).select_by_visible_text(u"regexp:E82 \\(2007\\s—\\s2013\\)")
        driver.find_element_by_css_selector("#auto-generation > option[value=\"3\"]").click()
        time.sleep(3)
        driver.find_element_by_id("filter-auto-car-mm-0").click()
        time.sleep(2)
        driver.find_element_by_css_selector(
            "#spare_condition > div.radio-button > label > span.link.link-dashed").click()
        time.sleep(2)
        driver.find_element_by_css_selector(
            "#auto-car-order > div.radio-button > label > span.link.link-dashed").click()

        # Наименование
        driver.find_element_by_id("spare_name").click()
        driver.find_element_by_id("spare_name").clear()
        driver.find_element_by_id("spare_name").send_keys(u"Тест")

        # Цена
        driver.find_element_by_id("price-user").click()
        time.sleep(1)

        # Текст объявления
        driver.find_element_by_id("text").click()
        time.sleep(3)
        driver.find_element_by_id("text").clear()
        driver.find_element_by_id("text").send_keys(u"Тестирую объявление")
        #driver.find_element_by_id("upload-btn").click()
        driver.find_element_by_id("upload-btn").clear()
        driver.find_element_by_id("upload-btn").send_keys(self.IMAGE_PATH + u"image.png")
        #driver.find_element_by_id("upload-btn").send_keys(Keys.ENTER)
        # driver.find_element_by_id("_phone[0]").send_keys(u"7")
        #time.sleep(1)
        #driver.find_element_by_id("_phone[0]").send_keys(u"707")
        #time.sleep(1)
        #driver.find_element_by_id("_phone[0]").send_keys(u"8179300")
        #time.sleep(1)
        driver.find_element_by_css_selector(
            "div.element-group.element-group-parameter-comments_allowed_for.element-group-xs.element-type-select.element-group-hint > div.group-element > div.field-container > div.selectbox.enabled > div.selectbox-select > div.text.selected").click()
        time.sleep(3)
        #driver.find_element_by_css_selector(
        #    "div.element-group.element-group-parameter-send_to_market.element-group-with-label.element-type-checkbox").click()
        #driver.find_element_by_id("send_to_market-checkbox-0").click()

        # Сабмит
        #driver.find_element_by_css_selector("input.js-submit").click()

    def save_captcha(self):
        driver = self.driver
        element = driver.find_element_by_class_name('captcha-image')
        res = ""
        if element:
            res = element.screenshot_as_base64
        return res

    def send_captcha(self, img_base):
        request_dict = {"clientId": self.CLIENT_ID,
                        "task": {
                            "type": "ImageToTextTask",
                            "body": img_base,
                            "phrase": False,
                            "case": False,
                            "numeric": True,
                            "math": 0,
                            "minLength": 5,
                            "maxLength": 5
                        }
                        }

        json_request = json.dumps(request_dict)
        # Послать капчу
        headers = {'Content-type': 'application/json'}
        response = requests.post("https://api.anti-captcha.com/createTask", data=json_request, headers=headers)
        # Находим и возвращаем taskId
        response_dict = json.loads(response.content)
        if response_dict["errorId"] == 0:
            return response_dict["taskId"]
        else:
            print response_dict["errorCode"]
            print response_dict["errorDescription"]
            return -1

    def ask_for_answer(self, task_id):
        request_dict = {"clientId": self.CLIENT_ID, "taskId": task_id}
        json_request = json.dumps(request_dict)
        # Послать капчу
        headers = {'Content-type': 'application/json'}
        response = requests.post("https://api.anti-captcha.com/getTaskResult", data=json_request, headers=headers)
        # Находим и возвращаем taskId
        response_dict = json.loads(response.content)
        if response_dict["errorId"] == 0:
            if response_dict["status"] == "ready":
                return response_dict["solution"]["text"]
            else:
                return 0
        else:
            print response_dict["errorCode"]
            print response_dict["errorDescripton"]
            return -1

    def captcha_processing(self, img_base):
        task_id = self.send_captcha(img_base)
        res = 0
        if task_id > 0:
            # Ждать ответа
            tries_left = 10
            while (res == 0) or (tries_left <= 0):
                time.sleep(2)
                tries_left -= 1
                res = self.ask_for_answer(task_id)
                if res < 0:
                    break

        return res

    def test_kolesa_kz(self):
        driver = self.driver
        driver.get("https://kolesa.kz/a/new/")

        self.fill_fields()
        if self.is_element_present("class name", "captcha-image"):
            img_data = self.save_captcha()

            if img_data != "":
                answer = self.captcha_processing(img_data)
                if answer <= 0:
                    print "Ошибка добавления строки №"
                else:
                    driver.find_element_by_id("advert-captcha").send_keys(answer)

        # driver.find_element_by_css_selector("input.js-submit").click()
        # driver.find_element_by_css_selector("div.payments__button.js-payment-button.motivation__button").click()
        # driver.find_element_by_css_selector("span.cabinet-decorated-link").click()
        # driver.find_element_by_link_text(u"Мои объявления").click()
        # driver.find_element_by_xpath("//li[4]/a/span").click()
        # driver.find_element_by_css_selector("div.a-info-expand").click()
        # driver.find_element_by_css_selector("div.col-sm-6.a-pay.a-pay-short.a-color-none").click()
        # driver.find_element_by_css_selector("div.col-sm-6.a-pay.a-pay-short.a-color-none").click()
        # driver.find_element_by_css_selector("div.a-info-expand").click()

    def is_element_present(self, how, what):
        try:
            self.driver.find_element(by=how, value=what)
        except NoSuchElementException as e:
            return False
        return True

    def is_alert_present(self):
        try:
            self.driver.switch_to_alert()
        except NoAlertPresentException as e:
            return False
        return True

    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally:
            self.accept_next_alert = True

    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)


if __name__ == "__main__":
    unittest.main()
