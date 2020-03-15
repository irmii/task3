import csv
import json
import os
import xml.etree.ElementTree as ET
import urllib3
from datetime import datetime

import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout, TooManyRedirects


# Позволяет игнорировать исключение InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_data_from_api(url):
    response = None
    try:
        raw_response = requests.get(url, verify=False)
        response = raw_response.text.replace('\n', '')
        raw_response.raise_for_status()
        # print(f'Последние данные из API: {get_data(response)}')
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except ConnectionError as conn_err:
        print(f'ConnectionError occurred: {conn_err}')
    except Timeout as time_err:
        print(f'Timeout error occurred: {time_err}')
    except TooManyRedirects as redir_err:
        print(f'TooManyRedirects error occurred: {redir_err}')
    finally:
        return response


def write(format_file: str, path: str, current_data: dict):
    """Запись в файл в зависимости от формата"""
    data_time = datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S")
    message = ['Данные в API не изменились, файл не обновлен', 'Данные обновлены']
    if os.path.exists(path):
        if format_file == 'csv':
            if check_csv(path, current_data):
                print(f'[{data_time}] {message[0]}')  # Данные не обновлены
            else:
                write_csv(current_data, path)
                print(f'[{data_time}] {message[1]}')
        elif format_file == 'json':
            if check_json(current_data, path):
                print(f'[{data_time}] {message[0]}')  # Данные не обновлены
            else:
                write_json(current_data, path)
                print(f'[{data_time}] {message[1]}')
        else:
            print('Некорретный формат вывода данных')
    else:
        if format_file == 'csv':
            create_csv(path)
            write_csv(current_data, path)
            print(f'[{data_time}] {message[1]}')
        elif format_file == 'json':
            create_json(current_data, path)
            print(f'[{data_time}] {message[1]}')
        else:
            print('Некорретный формат вывода данных')


def get_data(response_data):
    """Возвращает словарь с актуальными значениями из API, получает строку на вход.
    Возвращает словарь с необходимыми значениями"""
    root = ET.fromstring(response_data)  # TODO Exception
    data_dict = {}
    for element in root:
        if element.attrib['id'] == 'marketdata':
            for rows in element:
                if rows.tag == 'rows':
                    for row in rows:
                        data_dict['localtime'] = datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S")
                        data_dict['updatetime'] = row.attrib['UPDATETIME']
                        data_dict['open'] = row.attrib['OPEN']
                        data_dict['low'] = row.attrib['LOW']
                        data_dict['high'] = row.attrib['HIGH']
                        data_dict['last'] = row.attrib['LAST']
                        if row.attrib['OPEN'] == '':
                            data_dict['open'] = 'Нет данных в API'
                        if row.attrib['LOW'] == '':
                            data_dict['low'] = 'Нет данных в API'
                        if row.attrib['HIGH'] == '':
                            data_dict['high'] = 'Нет данных в API'
                        if row.attrib['LAST'] == '':
                            data_dict['last'] = 'Нет данных в API'
    return data_dict


# -------------------------------блок CSV------------------------------------


def write_csv(current_data, path):
    """Добавление записи в CSV формате"""
    csv_columns = ['localtime', 'updatetime', 'open', 'low', 'high', 'last']
    try:
        with open(path, "a", newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=csv_columns)
            writer.writerow(current_data)
    except IOError:
        print("I/O error")


def create_csv(path):
    """Создание CSV файла и запись заголовков"""
    csv_columns = ['localtime', 'updatetime', 'open', 'low', 'high', 'last']
    try:
        with open(path, "a", newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=csv_columns)
            writer.writeheader()
    except IOError:
        print("I/O error")


def check_csv(path, dict_of_data):
    """Получает на вход обхект файла CSV и проверяет последнее совпадение с новым значением из API
    Возвращает True, если значения совпадают"""
    flag = False
    array = []
    try:
        with open(path, "r") as csv_file:
            for row in csv_file:
                array.append(row)
    except IOError:
        print("I/O error")
    try:
        flag = array[-1].split(',')[-5] == dict_of_data['updatetime']
    except IndexError as err:
        print(f'Возможно, указан некорректный формат файла. Ошибка: {err}')
    return flag


# -------------------------------блок JSON------------------------------------


def create_json(current_data, path):
    array = [current_data]
    try:
        with open(path, "w", newline='') as json_file:
            json.dump(array, json_file, indent=4)
    except IOError:
        print("I/O error")


def write_json(current_data, path):
    data_json = read_json(path)
    array = get_list_objects(data_json)
    array.append(current_data)
    try:
        with open(path, "w", newline='') as json_file:
            json.dump(array, json_file, indent=4)
    except IOError:
        print("I/O error")


def check_json(current_data, path):
    """Возвращает True, если последние записи совпадают"""
    flag = False
    list_obj = get_list_objects(read_json(path))
    try:
        flag = list_obj[-1]['updatetime'] == current_data['updatetime']
    except Exception as err:
        print(f'Возможно, указан некорректный формат файла. Ошибка: {err}')
    return flag


def get_list_objects(data):  # формирует список словарей
    result = []
    for block in data:
        result.append(block)
    return result


def read_json(path):
    try:
        with open(path, "r") as json_file:
            try:
                data_json = json.load(json_file)
            except json.decoder.JSONDecodeError as err:
                print(f'Возможно, указан некорректный формат файла: {err}')
            else:
                return data_json
    except IOError:
        print("I/O error")
