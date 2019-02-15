

import sys, inspect

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