import argparse
import signal
import time

import moex

parser = argparse.ArgumentParser()
parser.add_argument('--format', '-format', '-f', help='Формат файла на выход')
parser.add_argument('--out', '-out', '-o', help='Полный путь к файлу')
parser.add_argument('--watch', '-watch', '-w', action="store_true")
parser.add_argument('--refresh', '-refresh', '-r', type=int, default=60)
args = parser.parse_args()
print(f'Формат записи: {args.format}. Путь к файлу: {args.out}')


def signal_handler(signal, frame):
    print(f'Выполнение завершено успешно. Нажмите Enter, чтобы выйти из консоли')
    input()
    quit()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)  # Обрабатывает CTRL + C
    URI = 'https://iss.moex.com/iss/engines/stock/markets/shares/securities/five.xml'
    if args.watch:
        print('Вы находитесь в режиме отслеживания')
        print(f'Периодичность запроса: {args.refresh} секунды')
        while True:
            response = moex.get_data_from_api(URI)
            try:
                moex.write(args.format, args.out, moex.get_data(response))
            except TypeError as err:
                print(f'Возможно, указан некорректный формат файла: {err}')
            time.sleep(args.refresh)
    else:
        print('Вы находитесь в режиме разового запроса')
        response = moex.get_data_from_api(URI)
        try:
            moex.write(args.format, args.out, moex.get_data(response))
        except TypeError as err:
            print(f'Возможно, указан некорректный формат файла: {err}')
