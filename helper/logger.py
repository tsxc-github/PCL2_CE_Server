from datetime import datetime
from colorama import Fore

def info(message: str):
    print(f"{Fore.WHITE}[{Fore.LIGHTYELLOW_EX}{datetime.now()}{Fore.WHITE}] [{Fore.GREEN}INFO{Fore.WHITE}] {message}")

def warn(message: str):
    print(f"{Fore.WHITE}[{Fore.LIGHTYELLOW_EX}{datetime.now()}{Fore.WHITE}] [{Fore.YELLOW}WARN{Fore.WHITE}] {message}")

def error(message: str):
    print(f"{Fore.WHITE}[{Fore.LIGHTYELLOW_EX}{datetime.now()}{Fore.WHITE}] [{Fore.RED}ERROR{Fore.WHITE}] {message}")

def debug(message: str):
    print(f"{Fore.WHITE}[{Fore.LIGHTYELLOW_EX}{datetime.now()}{Fore.WHITE}] [DEBUG] {message}")
