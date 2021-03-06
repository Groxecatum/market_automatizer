# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.by import By
import unittest
import time
import json
import requests
import csv


class KolesaKz(unittest.TestCase):
    IMAGE_PATH = u"/home/ysklyarov/"
    CLIENT_ID = "8b93bffe7deb2e25d36e7fff021bdb66"
    LOGIN = u"87017565078@mail.ru"
    PASS = u"satpaeva139"
    PHONE1 = "+7 (701) 756-50-78"
    PHONE2 = ""
    PHONE3 = ""

    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(10)
        self.base_url = "https://www.kolesa.kz/"
        self.verificationErrors = []
        self.accept_next_alert = True

    def login(self):
        driver = self.driver
        driver.get("https://id.kolesa.kz/login/?destination=https%3A%2F%2Fkolesa.kz%2Fmy%2F")
        # Мыло
        driver.find_element_by_id("email").click()
        driver.find_element_by_id("email").clear()
        driver.find_element_by_id("email").send_keys(self.LOGIN)
        # Пароль
        driver.find_element_by_id("password").click()
        driver.find_element_by_id("password").clear()
        driver.find_element_by_id("password").send_keys(self.PASS)

        driver.find_element_by_class_name("login-btn").click()

    def fill_fields(self, driver, row):
        print row[3].decode('utf-8')
        driver.execute_script("window.scrollTo(0, -document.body.scrollHeight);")
        # Тип
        #Select(driver.find_element_by_id("change-section-select")).select_by_visible_text(u"Запчасти")
        driver.find_element_by_css_selector("option[value=\"2\"]").click()
        time.sleep(2)
        driver.find_element_by_css_selector("option[value=\"spare.parts\"]").click()
        time.sleep(4)

        driver.execute_script("window.scrollTo(0, -document.body.scrollHeight);")
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
            Select(driver.find_element_by_id("auto-generation")).select_by_index(int(row[2].decode('utf-8')))
        time.sleep(2)
        # Состояние - новое или б\у
        driver.find_element_by_xpath("//div[@id='spare_condition']/div[2]/label").click()
        driver.find_element_by_xpath("//div[@id='auto-car-order']/div/label/span").click()
        # Цена
        driver.find_element_by_id("price-user").click()
        driver.find_element_by_id("price-user").clear()
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

        # Телефоны
        driver.find_element_by_name("_phone[0]").click()
        driver.find_element_by_name("_phone[0]").clear()
        driver.find_element_by_name("_phone[0]").send_keys(self.PHONE1)
        time.sleep(1)

        if self.PHONE2 != "":
            driver.find_element_by_name("_phone[1]").click()
            driver.find_element_by_name("_phone[1]").clear()
            driver.find_element_by_name("_phone[1]").send_keys(self.PHONE2)
            time.sleep(1)

        if self.PHONE3 != "":
            driver.find_element_by_name("_phone[2]").click()
            driver.find_element_by_name("_phone[2]").clear()
            driver.find_element_by_name("_phone[2]").send_keys(self.PHONE3)
            time.sleep(1)

        # Кто комментирует?
        driver.find_element_by_xpath("//div[20]/div/div/div/div/div").click() # Не работает с зареганным магазином
        driver.find_element_by_xpath("//div[20]/div/div/div/ul/li[4]").click()
        time.sleep(1)

    def save_captcha(self, driver):
        driver.execute_script("window.scrollTo(0, -document.body.scrollHeight);")
        element = driver.find_element_by_xpath("/html/body/main/div/div[3]/div/form/div[2]/div[23]/div/div/div/img")#find_element_by_class_name('captcha-image')
        res = ""
        if element:
            res = element.screenshot_as_base64
            #element.screenshot('/home/ysklyarov/shot.png')
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

    def handle_alert(self, driver):
        try:
            alert = driver.switch_to.alert
            if alert:
                alert.accept()
                time.sleep(3)
        except NoAlertPresentException:
            pass
        except Exception as e:
            print e.message

    def test_kolesa_kz(self):
        self.login()

        driver = self.driver
        with open('data.csv', 'rb') as csvfile:
            with open('failed.csv', 'wb+') as fails_log:
                reader = csv.reader(csvfile, delimiter=';', quotechar='"')
                failures_writer = csv.writer(fails_log, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                header = True
                for row in reader:
                    try:
                        if header:
                            header = False
                            continue   #пропускаем хедер

                        driver.get("https://kolesa.kz/a/new/")

                        # Остался запрос "Уйти со страницы?"
                        self.handle_alert(driver)

                        self.fill_fields(driver, row)

                        if self.is_element_present(By.ID, "advert-captcha"):
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
                        time.sleep(5)
                    except Exception as e:
                        print e
                        failures_writer.writerow(row)
                        fails_log.flush()
                        continue


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