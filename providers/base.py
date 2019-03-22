

import os, sys, inspect
from selenium import webdriver
from contextlib import contextmanager

gobal_option_headless = False

class ProviderPlugin():    
    def get_browser():
        pass # return selenium browser ready for scrape

def get_provider_classes():

    class_list = []

    m = sys.modules['providers']
    for module_name, module_obj in inspect.getmembers(m):
        if inspect.ismodule(module_obj):
            for name, obj in inspect.getmembers(module_obj):
                if inspect.isclass(obj):
                    if issubclass(obj, ProviderPlugin) and name!='ProviderPlugin':
                        class_list.append(obj)

    return class_list

@contextmanager
def selenium_webdriver():
    # Return webscraping webdriver (selenium)
    # Look for chromedriver in the same folder
    this_script_path = os.path.dirname(os.path.realpath(__file__))
    chromedriverpath = os.path.join(this_script_path, '..', 'chromedriver')
    if not os.path.exists(chromedriverpath):
        raise Exception('Chromedriver not installed at ' + chromedriverpath)

    chrome_options = webdriver.chrome.options.Options()
    if gobal_option_headless:
        chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(chromedriverpath, chrome_options=chrome_options)

    try:
        yield driver
    finally:
        driver.quit()    