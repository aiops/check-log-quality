from importlib import import_module
import logging
import subprocess
import sys
import argparse

def _install_module(module_name, quality_type):
    module_endpoint = \
        'https://github.com/aiops/log-qualitiy-models/raw/main/' + \
        quality_type + "_quality" + '/' + module_name + '/dist/' + module_name + \
        '-1.0-py3-none-any.whl?raw=true'
    
    try:
        command = [sys.executable, "-m", "pip", "install", module_endpoint]
        completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    except subprocess.CalledProcessError as e:
        logging.error("Error occured while pip-installing dependency %s from %s", module_name, module_endpoint)
        logging.error("pip-command return code: %s", e.returncode)
        logging.error("pip-command output: %s", e.stdout)
        raise e
    else:
        logging.info("Module %s successfully installed.", module_name)
        logging.debug("pip command output: %s", completed.stdout)


def _instantiate_class(module, class_name):
    class_ = getattr(module, class_name)
    class_instance = class_()
    return class_instance


def import_model(module_name, class_name, quality_type):
    model_class = None

    sub_module_name = module_name + "." + module_name
    try:
        module = import_module(module_name)
    except:
        logging.warning("Model %s locally not available. Trying to install it...", sub_module_name)
        try:
            _install_module(module_name, quality_type)
            module = import_module(module_name)
        except Exception as e:
            logging.error("Unable to import module %s.", module_name)
            raise e

    try:
        sub_module = import_module(sub_module_name)
    except:
        logging.warning("Sub-module %s not found. Using module %s.", sub_module_name, module_name)
    else:
        module = sub_module
        module_name = sub_module_name

    try:
        model_class = _instantiate_class(module, class_name)
    except Exception as e:
        logging.error("Failed to load model class %s from module %s.", class_name, module_name)
        raise e

    return model_class


def setup_command_line_arg():
    parser = argparse.ArgumentParser(description='Parse logs from source code.')

    parser.add_argument('-i', '--input', type=str, required=True, help="input file path to read")
    parser.add_argument('--quality_module_level', default="level_qulog_sm_rf", type=str, required=False, help="module for log level quality")
    parser.add_argument('--quality_class_level', default="LevelQulogSmRf", type=str, required=False, help="class name for log level quality")
    parser.add_argument('--quality_module_ling', default="ling_qulog_sm_rf", type=str, required=False, help="module for log linguistic quality")
    parser.add_argument('--quality_class_ling', default="LingQulogSmRf", type=str, required=False, help="class name for log linguistic quality")

    return parser.parse_args()