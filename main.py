# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
import unittest
import time
import json
import requests
import csv


class KolesaKz(unittest.TestCase):
    IMAGE_PATH = u"/home/ysklyarov/"
    CAPTCHA_SIZE = 40
    CLIENT_ID = "8b93bffe7deb2e25d36e7fff021bdb66"

    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)
        self.base_url = "https://www.kolesa.kz/"
        self.verificationErrors = []
        self.accept_next_alert = True

    def login(self):
        driver = self.driver
        driver.get("https://id.kolesa.kz/login/?destination=https%3A%2F%2Fkolesa.kz%2Fmy%2F")
        # Мыло
        driver.find_element_by_id("email").click()
        driver.find_element_by_id("email").clear()
        driver.find_element_by_id("email").send_keys(u"pupenkoff@bk.ru")
        # Пароль
        driver.find_element_by_id("password").click()
        driver.find_element_by_id("password").clear()
        driver.find_element_by_id("password").send_keys(u"123456Qw")

        driver.find_element_by_class_name("login-btn").click()

    def fill_fields(self, driver, row):
        # Тип
        Select(driver.find_element_by_id("change-section-select")).select_by_visible_text(u"Запчасти")
        driver.find_element_by_css_selector("option[value=\"2\"]").click()
        time.sleep(2)
        driver.find_element_by_css_selector("option[value=\"spare.parts\"]").click()
        time.sleep(4)

        # Наименование
        driver.find_element_by_id("spare_name").click()
        driver.find_element_by_id("spare_name").clear()
        driver.find_element_by_id("spare_name").send_keys(unicode(row[3].decode('utf-8')))
        #time.sleep(3)

        # Марка
        Select(driver.find_element_by_id("auto-car-mm-0")).select_by_visible_text(row[0].decode('utf-8'))
        time.sleep(2)
        if row[1] != "":
            Select(driver.find_element_by_id("auto-car-mm-1")).select_by_visible_text(row[1].decode('utf-8'))
        time.sleep(2)
        if row[2] != "":
            Select(driver.find_element_by_id("auto-generation")).select_by_visible_text(row[2].decode('utf-8'))
        time.sleep(2)
        # Состояние - новое или б\у
        driver.find_element_by_xpath("//div[@id='spare_condition']/div[2]/label").click()
        driver.find_element_by_xpath("//div[@id='auto-car-order']/div/label/span").click()
        # Цена
        driver.find_element_by_id("price-user").click()
        driver.find_element_by_id("price-user").send_keys(row[5].decode('utf-8'))
        #time.sleep(1)

        # Текст объявления
        driver.find_element_by_id("text").click()
        driver.find_element_by_id("text").clear()
        driver.find_element_by_id("text").send_keys(row[4].decode('utf-8'))
        #time.sleep(3)

        # Картинка
        if row[6] != "":
            driver.find_element_by_id("upload-btn").clear()
            driver.find_element_by_id("upload-btn").send_keys(self.IMAGE_PATH + row[6].decode('utf-8'))

        # Город
        driver.find_element_by_xpath("//div[12]/div/div/div/div/div").click()
        driver.find_element_by_xpath("//div[12]/div/div/div/ul/li[5]").click()

        # Телефон
        driver.find_element_by_name("_phone[0]").click()
        driver.find_element_by_name("_phone[0]").clear()
        driver.find_element_by_name("_phone[0]").send_keys("+7 (707) 817-93-00")
        time.sleep(1)

        # Кто комментирует?
        driver.find_element_by_xpath("//div[20]/div/div/div/div/div").click()
        driver.find_element_by_xpath("//div[20]/div/div/div/ul/li[4]").click()
        time.sleep(3)

    def save_captcha(self, driver):
        driver.execute_script("window.scrollTo(0, -document.body.scrollHeight);")
        element = driver.find_element_by_class_name('captcha-image')
        res = ""
        if element:
            res = element.screenshot_as_base64
            element.screenshot('/home/ysklyarov/shot.png')
        return res

    def send_captcha(self, img_base):
        request_dict = {"clientKey": self.CLIENT_ID,
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
        response = requests.post("https://api.anti-captcha.com/createTask", data=json_request)
        # Находим и возвращаем taskId
        response_dict = json.loads(response.content)
        if response_dict["errorId"] == 0:
            return response_dict["taskId"]
        else:
            print response_dict["errorCode"]
            print response_dict["errorDescription"]
            return -1

    def ask_for_answer(self, task_id):
        request_dict = {"clientKey": self.CLIENT_ID, "taskId": task_id}
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
        self.login()

        driver = self.driver
        driver.get("https://kolesa.kz/a/new/")

        with open('data.csv', 'rb') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            header = True
            for row in spamreader:
                if header:
                    header = False
                    continue   #пропускаем хедер
                self.fill_fields(driver, row)
                if self.is_element_present("class name", "captcha-image"):
                    img_data = self.save_captcha(driver)

                    if img_data != "":
                        answer = self.captcha_processing(img_data)
                        if answer <= 0:
                            print "Ошибка добавления строки №"
                        else:
                            driver.find_element_by_id("advert-captcha").send_keys(answer)
                # Сабмит
                driver.find_element_by_css_selector("input.js-submit").click()
                driver.find_element_by_css_selector("div.payments__button.js-payment-button.motivation__button").click()
                driver.find_element_by_css_selector("span.cabinet-decorated-link").click()
                time.sleep(20)

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
