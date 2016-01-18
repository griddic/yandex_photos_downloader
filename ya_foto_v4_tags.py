# -*- coding: utf-8 -*-
__author__ = 'GRIDDIC'

from selenium import webdriver
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
import urllib, urllib2
from selenium.webdriver.common.action_chains import ActionChains
import sys
import json
import operator
import io
import ctypes
from datetime import  datetime
SPI_SETDESKWALLPAPER = 20


#IMAGES_FOLDER = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'images_tag_test')
IMAGES_FOLDER = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'images')
if not os.path.exists(IMAGES_FOLDER):
    os.makedirs(IMAGES_FOLDER)
print "Images will be downloaded in %s" % (IMAGES_FOLDER, )
#time.sleep(10)


def get_folder_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def ignore_errors(fun):
    def res(*args, **kwargs):
        try:
            return fun(*args, **kwargs)
        except:
            return None
    return res

class Connect:
    def __init__(self, url, attempts=5, timeout=5):
        assert attempts > 0 and timeout > 0, "Timeout and attempts should be positive."
        cromedriver = "D:\chromedriver.exe"
        #self.connection = webdriver.Firefox()
        #self.connection = webdriver.Opera()
        #os.environ["webdriver.chrome.driver"] = chromedriver
        print "get new attantion to open Crome"
        #raw_input()
        self.connection = webdriver.Chrome(cromedriver)
        print "Crome launced succesfully."
        while attempts - 1:
            try:
                self.connection.get(url)
                return
            except:
                print "Can't connect to {url}".format(url = url)
            finally:
                attempts -= 1
        self.connection.get(url)

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        #pass
        self.connection.close()

def click_by_css(window, selector):
    region = WebDriverWait(window, 60).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )
    region.click()


def move_to_random_photo(window):
    window.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    click_by_css(window, '.stream-image.is-loaded')

def name_by_url(url):
    assert isinstance(url, basestring)
    key_word = 'popular'
    key_word_position = url.find(key_word)
    if key_word_position == -1:
        name = url
    else:
        name = url[key_word_position + len(key_word) + 1:]
    name = name.replace('/', '_')
    words = name.split('_')
    name = name = '_'.join(words[:-2] + [words[-1]])
    print "  %s  " % (name, )
    return name
    #return name.replace('/', '_').replace("fullscreen", "view")

class CyclicValuess:
    def __init__(self, values):
        self.values = values
        self.index = 0
    def next(self):
        self.index = (self.index + 1) % len(self.values)
        return self
    def get(self):
        return self.values[self.index]

class TimeOutError(Exception):
    pass

class Delay:
    def __init__(self, value=1):
        self.delay = value

    def increase(self):
        if self.delay > 500:
            os.system('echo %s >> timings.txt'%(datetime.now()))
            raise TimeOutError
        self.delay = self.delay + 1
        return self()

    def decrease(self):
        self.delay = (self.delay + 1) / 2
        #self.delay = 1
        return self()

    def __call__(self, *args, **kwargs):
        return self.delay

    def __str__(self):
        return str(self())

    def __float__(self):
        return float(self())

#CSS_BY_DIRECTION = {'forward':".photo-ears__right.js-next",
#                    'backward':".photo-ears__left.js-prev"}
CSS_BY_DIRECTION = {'forward': ".photo-ears__right.js-next",
                    'backward': ".photo-ears__left.js-prev"}
def go_to_next_picture(driver, once=False, direction=CyclicValuess(CSS_BY_DIRECTION.keys())):
    print "Go %s.  " % (direction.get(),)

    cur_url = driver.current_url

    if once:
        time.sleep(2)
        click_by_css(driver, CSS_BY_DIRECTION[direction.get()])
        return

    try:
        click_by_css(driver, CSS_BY_DIRECTION[direction.get()])
    except:
        direction.next()
        go_to_next_picture(driver, once=True)
        return

    if cur_url == driver.current_url:
        print "No way %s " % (direction.get(), )
        direction.next()
        go_to_next_picture(driver, once=True)


class NoMenuBottom(Exception):
    pass


def click_menu_button(driver):
    i = 5
    while i:
        try:
            menu = driver.find_element_by_css_selector(".icon.icon_pseudo.icon_more")
            if not menu.is_displayed():
                raise
            menu.click()
            return
            break
        except:
            driver.refresh()
            time.sleep(2)
            i -= 1
    raise NoMenuBottom




def download_yandex_image(browser, url, pic_name):
    #returnal = browser.current_window_handle
    browser.get(url)
    chain = ActionChains(browser)
    img = browser.find_element_by_xpath('//img')
    chain.click(img)
    chain.perform()
    im_url = browser.find_element_by_xpath('//img').get_attribute('src')

    urllib.urlretrieve(im_url, pic_name)
    browser.back()
    return pic_name

def find_brackets_sequence(string, begin=0):
    count = 0
    in_seq = 0
    i = begin
    while i < len(string):
        if string[i] == '"':
            i += 1
            while string[i] != '"':
                i += 1
        if string[i] == "(":
            in_seq = True
            count += 1
            if not in_seq:
                begin = i
        elif string[i] == ')':
            count -= 1
            if count == 0:
                return begin, i + 1
        i += 1

    raise Exception('Incorrect sequence.')


def get_url_of_original_picture(cur_url):
    response = urllib2.urlopen(cur_url)
    data = response.read()
    try:
        #data = str(data)
        begin = data.find(".restoreModel(", data.find("ns.Model.get('photo'")) + len(".restoreModel(") - 1
        begin, end = find_brackets_sequence(data, begin)
        try:
            parameters_dict = json.loads(data[begin + 1:end -1])
        except:
            with open('data.json', 'w') as outt:
                outt.write(data[begin + 1:end -1])
            raise
        biggest_key = sorted([(k, v['width']) for k, v in parameters_dict['sizes'].items()], key=operator.itemgetter(1), reverse=True)[0][0]
        return parameters_dict['sizes'][biggest_key]['url'], parameters_dict['imageFormat']
    except:
        with open("bad_url.xml",'w') as outt:
            outt.write(data)
        raise


def get_tags_by_url(url):
    response = urllib2.urlopen(url)
    data = response.read()
    try:
        tags = set()
        begin = data.find("Метки")
        closing = data.find("</div>", begin)
        while begin < closing:
            tag_begin = data.find('data-tag-name="', begin)
            if tag_begin == -1:
                break
            tag_begin = tag_begin + len('data-tag-name="')
            tag = data[tag_begin: data.find('"', tag_begin)]
            tags.add(tag)
            #print begin, tag, tag_begin, closing
            begin = tag_begin + len(tag)

            #raw_input()
        return tags
    except:
        with open("bad_url_wrapper.xml",'w') as outt:
            outt.write(data)
        raise


def clear_console():
    clear = lambda: os.system('cls')
    clear()


def rewrite(string):
    clear_console()
    sys.stdout.write('\r%s' % (string, ))


def write(string):
    sys.stdout.write('%s' % (string, ))


def write_info(file_name, tags, url):
    d = {}
    d['url'] = url
    d['tags'] = list(tags)
    string = json.dumps(d).decode('unicode-escape')
    with io.open(file_name, 'w') as outt:
        outt.write(string)

@ignore_errors
def set_to_desktop_background(path_to_image):
    ctypes.windll.user32.SystemParametersInfoA(SPI_SETDESKWALLPAPER, 0, r'%s' % (str(path_to_image), ), 0)

if __name__ == "__main__":
    if not os.path.exists(IMAGES_FOLDER):
        os.makedirs(IMAGES_FOLDER)
    while True:
        try:
            with Connect("https://fotki.yandex.ru/next/popular") as window:
                move_to_random_photo(window)
                #click_by_css(window, ".ghost-button.js-layout-toggle")
                delay = Delay()
                while True:
                    time.sleep(delay)
                    clear_console()
                    print "delay = %s.  " % (delay, )
                    name = name_by_url(window.current_url)
                    #tags = get_tags_by_url(window.current_url)
                    try:
                        force_quit = False
                        original_url, pic_format = get_url_of_original_picture(window.current_url)
                        tags_name = name + '.json'
                        name = name + '.' + pic_format
                        if name in os.listdir(IMAGES_FOLDER):
                            print "Image has already been downloaded. "
                            if tags_name not in os.listdir(IMAGES_FOLDER):
                                tags = get_tags_by_url(window.current_url)
                                write_info(os.path.join(IMAGES_FOLDER, tags_name), tags, window.current_url)
                            #go_to_next_picture(window)
                            delay.increase()
                            continue
                        download_yandex_image(window, original_url, os.path.join(IMAGES_FOLDER, name))
                        set_to_desktop_background(os.path.join(IMAGES_FOLDER, name))
                        tags = get_tags_by_url(window.current_url)
                        write_info(os.path.join(IMAGES_FOLDER, tags_name), tags, window.current_url)
                        delay.decrease()
                    except TimeOutError:
                        raise
                    except KeyboardInterrupt:
                        force_quit = True
                        raise
                    except:
                        #raise
                        print "CANT DOWNLOAD: %s " % (window.current_url,)
                    finally:
                        #pass
                        if not force_quit:
                            go_to_next_picture(window)
        except KeyboardInterrupt:
            break
        except:
            #raise
            pass

