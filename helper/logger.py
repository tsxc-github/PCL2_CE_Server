from datetime import datetime
from colorama import Fore, Back , Style

def info(message):
    print(f"{Fore.WHITE}[{Fore.LIGHTYELLOW_EX}{datetime.now()}{Fore.WHITE}] [{Fore.GREEN}INFO{Fore.WHITE}] {message}")

def warn(message):
    print(f"{Fore.WHITE}[{Fore.LIGHTYELLOW_EX}{datetime.now()}{Fore.WHITE}] [{Fore.YELLOW}WARN{Fore.WHITE}] {message}")

def error(message):
    print(f"{Fore.WHITE}[{Fore.LIGHTYELLOW_EX}{datetime.now()}{Fore.WHITE}] [{Fore.RED}ERROR{Fore.WHITE}] {message}")

def debug(message):
    print(f"{Fore.WHITE}[{Fore.LIGHTYELLOW_EX}{datetime.now()}{Fore.WHITE}] [DEBUG] {message}")
