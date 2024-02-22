import re
import shutil
import pickle
import atexit
import pickle as p
from pathlib import Path
from datetime import datetime
from collections import UserDict
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
import sys
import pygame

UKRAINIAN_SYMBOLS = 'абвгдеєжзиіїйклмнопрстуфхцчшщьюя'
TRANSLATION = (
    "a", "b", "v", "g", "d", "e", "je", "zh", "z", "y", "i", "ji", "j", "k", "l", "m", "n", "o", "p", "r", "s", "t",
    "u",
    "f", "h", "ts", "ch", "sh", "sch", "", "ju", "ja")
TRANS = {}
for key, value in zip(UKRAINIAN_SYMBOLS, TRANSLATION):
    TRANS[ord(key)] = value
    TRANS[ord(key.upper())] = value.upper()

images_files = list()
video_files = list()
documents_files = list()
audio_files = list()
archives_files = list()
folders = list()
other = list()
unknown = set()
extensions = set()

image_extensions = ['JPEG', 'PNG', 'JPG', 'SVG']
video_extensions = ['AVI', 'MP4', 'MOV', 'MKV']
audio_extensions = ['MP3', 'OGG', 'WAV', 'AMR']
documents_extensions = ['DOC', 'DOCX', 'TXT', 'PDF', 'XLSX', 'PPTX']
archives_extensions = ['ZIP', 'GZ', 'TAR']

list_of_all_extensions = (
        image_extensions + video_extensions +
        audio_extensions + documents_extensions +
        archives_extensions
)

registered_extensions = dict()
registered_extensions.update({i: 'images' for i in image_extensions})
registered_extensions.update({i: 'video' for i in video_extensions})
registered_extensions.update({i: 'audio' for i in audio_extensions})
registered_extensions.update({i: 'documents' for i in documents_extensions})
registered_extensions.update({i: 'archives' for i in archives_extensions})


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Field2:
    def __init__(self, value):
        self.__value = None
        self.value = value

    def is_valid(self, value):
        return True

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        if self.is_valid(value):
            self.__value = value
        else:
            raise ValueError("Invalid value")

    def __str__(self):
        return str(self.__value)


class Birthday(Field):
    def __init__(self, value):
        self.__value = None
        self.value = value

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        if is_valid_birthday(value):
            day, month, year = value.split(".")
            new_value = datetime(day=int(day), month=int(month), year=int(year))
            self.__value = new_value
        else:
            raise ValueError("Invalid value birthday")

    def __repr__(self):
        return f'{self.value.strftime("%d %B %Y")}'


class Email(Field2):
    def is_valid(self, email):
        if email is None:
            return True
        pattern = r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{v2,}'
        return re.match(pattern, email) is not None


class Notes(Field2):
    def __init__(self, value) -> None:
        self.__value = None
        self.value = value

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        self.__value = value


class Address(Field2):
    # def __init__(self, value) -> None:
    #     self._value = None
    #     self.value = value
    pass


class Name(Field):
    def __init__(self, value) -> None:
        self.__value = None
        self.value = value

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        self.__value = value


class Phone(Field):
    def __init__(self, value):
        self.__value = None
        self.value = value

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        if is_valid_phone(value) and value.isdigit() and len(value) == 10:
            self.__value = value
        else:
            raise ValueError

    def __repr__(self):
        return f'{self.value}'


class Record:
    def __init__(self, name, phone=None, birthday=None, email=None, address=None, notes=None):
        self.name = Name(name)
        self.phones = [Phone(phone)] if phone else []
        self.birthday = Birthday(birthday) if birthday else None
        self.email = Email(email)
        self.address = Address(address)
        self.notes = Notes(notes) if notes else None

    def days_to_birthday(self, current_date=None):
        if not current_date:
            current_date = datetime.now().date()
        if self.birthday:
            next_birthday = datetime.strptime(str(self.birthday), '%d.%m.%Y').date().replace(year=current_date.year)
            if current_date > next_birthday:
                next_birthday = next_birthday.replace(year=current_date.year + 1)
            days_remaining = (next_birthday - current_date).days
            return f"Days till the next Birthday for {self.name}: {days_remaining} days"
        else:
            return "Birth date not added"

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                self.phones.remove(p)
                return
        raise ValueError

    def edit_phone(self, old_phone, new_phone):
        for i in self.phones:
            if i.value == old_phone:
                i.value = new_phone
                return f'Number {old_phone} from {self.name}\'s list changed to {new_phone}'
            else:
                raise ValueError(f'phone {old_phone} is not find for name {self.name}')
        return f'Number {old_phone} is not exist in {self.name} list'

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def __str__(self):
        return (f"{self.name}\t{', '.join(str(p) for p in self.phones)}\t{self.birthday}\t{self.email}\t{self.address}")


class AddressBook(UserDict):
    def __init__(self):
        super().__init__()
        self.notes = []

    def search_contact(self, query):
        matching_contacts = list()
        # Check if the query matches any phone numbers
        for record in self.data.values():
            for phone in record.phones:
                if query in phone.value:
                    matching_contacts.append(record)
                    break
        # Check if the query matches any names
        for record in self.data.values():
            if query.lower() in record.name.value.lower():
                matching_contacts.append(record)
        return matching_contacts

    def __init__(self):
        super().__init__()
        self.notes = []

    def add_record(self, record):
        self.data[record.name.value] = record

    def save_notes(self, filename='notes.pickle'):
        with open(filename, 'wb') as file:
            pickle.dump(self.notes, file)

    def load_notes(self, filename='notes.pickle'):
        try:
            with open(filename, 'rb') as file:
                self.notes = pickle.load(file)
        except FileNotFoundError:
            print("No notes found.")

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def save_data_to_disk(self, filename='address_book.pickle'):
        with open(filename, 'wb') as file:
            p.dump(self.data, file)

    def load_data_from_disk(self, filename='address_book.pickle'):
        try:
            with open(filename, 'rb') as file:
                self.data = p.load(file)
        except FileNotFoundError:
            return f'file {func_delete} not find.'

    def __str__(self) -> str:
        return "\n".join(str(r) for r in self.data.values())


def input_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (TypeError, KeyError, ValueError, IndexError) as e:
            return type(e).__name__, e
            # return f"Error: {e}"

    return wrapper


@input_error
def add_note(title, content, tag=None):
    address_book.notes.append({"title": title, "content": content, "tag": tag})
    return "Note successfully added!"


@input_error
def view_notes():
    if not address_book.notes:
        return "No available notes."
    else:
        for i, note in enumerate(address_book.notes):
            print(f"\nNote {i + 1}:")
            print(f"Title: {note['title']}")
            print(f"Content: {note['content']}")
            print(f"Tag: {note.get('tag', 'No Tag')}")


@input_error
def search_by_tag(*tag):
    if not tag:
        tag_to_search = input("Enter the tag to search for: ")
    else:
        tag_to_search = tag[0]

    matching_notes = [note for note in address_book.notes if note.get('tag') == tag_to_search]

    if matching_notes:
        print(f"\nFound notes with tag '{tag_to_search}':")
        for i, note in enumerate(matching_notes):
            print(f"\nNote {i + 1}:")
            print(f"Title: {note['title']}")
            print(f"Text: {note['content']}")
            print(f"Tag: {note.get('tag', 'No Tag')}")
    else:
        print(f"No notes found with tag '{tag_to_search}'.")


@input_error
def edit_note(note_index_str, new_content):
    note_index = int(note_index_str) - 1  # Convert index to integer
    if 0 <= note_index < len(address_book.notes):
        address_book.notes[note_index]["content"] = new_content
        return "Note edited successfully!"
    else:
        return "Invalid note index. Please provide a valid index."


@input_error
def remove_note(note_index_str):
    note_index = int(note_index_str) - 1  # Convert index to integer
    if 0 <= note_index < len(address_book.notes):
        del address_book.notes[note_index]
        return "Note removed successfully!"
    else:
        return "Invalid note index. Please provide a valid index."


@input_error
def func_search_contacts(*args):
    query = args[0]
    matching_contacts = address_book.search_contact(query)

    if matching_contacts:
        result = '\n'.join(str(record) for record in matching_contacts)
        return f'Matching contacts: \n{result}'
    else:
        return f'No contacts found for query: {query}'


@input_error
def is_valid_phone(phone):
    pattern = r'\d{10}'
    searcher = re.findall(pattern, str(phone))
    phone = searcher[0]
    if phone == searcher[0]:
        return True
    else:
        return False


@input_error
def is_valid_birthday(value):
    pattern = r'\d{v2}\.\d{v2}\.\d{4}'
    search = re.findall(pattern, value)
    if value == search[0]:
        day, month, year = value.split(".")
        try:
            new_value = datetime(day=int(day), month=int(month), year=int(year))
            return True
        except ValueError:
            return False
    else:
        return False


@input_error
def func_add_name_phones(name, *phone_numbers):  # function for add name and phone
    if not address_book.find(name):
        record = Record(name)
    else:
        record = address_book.find(name)
    for phone_number in phone_numbers:
        record.add_phone(phone_number)
    address_book.add_record(record)
    return "Info saved successfully."


@input_error
def func_change_info(name, info_type, *args):
    record = address_book.find(name)
    if not record:
        return f"Contact '{name}' not found."

    if info_type.lower() == 'phone':
        old_phone, new_phone = args
        return record.edit_phone(old_phone, new_phone)

    elif info_type.lower() == 'email':
        new_email = args[0]
        record.email = new_email
        address_book.add_record(record)
        return f"Email for '{name}' changed to '{new_email}'."

    elif info_type.lower() == 'birthday':
        new_birthday = args[0]
        record.birthday.value = new_birthday
        address_book.add_record(record)
        return f"Birthday for '{name}' changed to '{new_birthday}'."

    else:
        return f"Invalid information type: {info_type}."


@input_error
def func_delete_info(name, info_type, *args):
    record = address_book.find(name)
    if not record:
        return f"Contact '{name}' not found."

    if info_type.lower() == 'phone':
        phone_to_delete = ' '.join(args)
        print("Phone to delete:", phone_to_delete)
        try:
            record.remove_phone(phone_to_delete)
            address_book.add_record(record)
            return f"Phone number '{phone_to_delete}' deleted for '{name}'."
        except ValueError:
            return f"Phone number '{phone_to_delete}' not found for '{name}'."

    elif info_type.lower() == 'email':
        record.email = None
        address_book.add_record(record)
        return f"Email deleted for '{name}'."

    elif info_type.lower() == 'birthday':
        record.birthday = None
        address_book.add_record(record)
        return f"Birthday deleted for '{name}'."

    else:
        return f"Invalid information type: {info_type}."


@input_error
def parser(user_input: str):
    user_input = user_input.title()
    for kw, command in COMMANDS.items():
        if user_input.startswith(kw):
            return command, user_input[len(kw):].strip().split()
    return func_unknown_command, []


@input_error
def func_add(*args):  # function for add name and phone
    name = args[0]
    record = Record(name)
    phone_numbers = args[1:]
    for phone_number in phone_numbers:
        record.add_phone(phone_number)
    address_book.add_record(record)
    return "Info saved successfully."


def func_add_email(name, email):
    if not address_book.find(name):
        record = Record(name, email=email)
    else:
        record = address_book.find(name)
    record.email = email
    address_book.add_record(record)
    return "Email saved successfully."


def func_add_birthday(name, birthday):
    if not address_book.find(name):
        record = Record(name, birthday=birthday)
    else:
        record = address_book.find(name)
        record.birthday = Birthday(birthday)

    address_book.add_record(record)
    return "Birthday saved successfully."


@input_error
def func_add_address(name, *address):  # function for add address
    if not address_book.find(name):
        record = Record(name, address=address)
    else:
        record = address_book.find(name)
        record.address = list(address)

    address_book.add_record(record)
    return "Info saved successfully."


@input_error
def func_change(*args):
    for k, v in address_book.items():
        if k == args[0]:
            rec = address_book[args[0]]
            return rec.edit_phone(args[1], args[2])
    return f'{args[0]} isn`t exist in list of names'


@input_error
def func_delete(*args):
    name = args[0]
    if name in address_book:
        address_book.delete(name)
        return f"User {name} has been deleted from the phone book"
    else:
        return f'User {name} is not in the address book'


@input_error
def func_search(*args):  # шукає інформацію про користувачів за декілька символів
    name = args[0]
    record = address_book.find(name)
    if record:
        return str(record)
    else:
        raise KeyError


@input_error
def func_show_all(*args):
    return str(address_book)


@input_error
def func_unknown_command():
    return "Unknown command. Try again."


@input_error
def func_hello():
    return "How can I help you?"


@input_error
def func_exit():
    address_book.save_data_to_disk()
    return "Good bye!"


def normalize(name: str) -> str:
    name, *extension = name.split('.')
    new_name = name.translate(TRANS)
    new_name = re.sub(r'\W', '_', new_name)
    return f"{new_name}.{'.'.join(extension)}"


def get_extensions(file_name):
    return Path(file_name).suffix[1:].upper()


def scan(folder):
    for item in folder.iterdir():
        if item.is_dir():
            if item.name not in list_of_all_extensions:
                folders.append(item)
                scan(item)
            continue

        extension = get_extensions(file_name=item.name)
        new_name = folder / item.name
        if not extension:
            other.append(new_name)
        else:
            try:
                container = registered_extensions[extension]
                extensions.add(extension)
                globals()[container + "_files"].append(new_name)
            except KeyError:
                unknown.add(extension)
                other.append(new_name)


def handle_file(path, root_folder, dist):
    target_folder = root_folder / dist
    target_folder.mkdir(exist_ok=True)

    new_name = normalize(path.name)
    new_path = target_folder / new_name

    print(f"Moving {path} to {new_path}")

    if path.exists():
        path.replace(new_path)
    else:
        print(f"Error: File {path} not found.")


def handle_archive(path, root_folder, dist):
    target_folder = root_folder / dist
    target_folder.mkdir(exist_ok=True)
    new_name = normalize(path.name.replace(".zip", '').replace('.tar', '').replace('.gz', ''))
    archive_folder = target_folder / new_name
    archive_folder.mkdir(exist_ok=True)

    try:
        shutil.unpack_archive(str(path.resolve()), str(archive_folder.resolve()))
    except shutil.ReadError:
        archive_folder.rmdir()
        path.unlink()
        return
    except FileNotFoundError:
        archive_folder.rmdir()
        path.unlink()
        return
    path.unlink()


def remove_empty_folders(path):
    for item in path.iterdir():
        if item.is_dir():
            remove_empty_folders(item)

    try:
        path.rmdir()
        print(f"Removed empty folder: {path}")
    except OSError as e:
        print(f"Error removing folder {path}: {e}")


def do_sort_folder(*args):
    folder_path = Path(args[0])
    print(folder_path)
    scan(folder_path)

    print(f'Start in {folder_path}')

    file_types = {
        'images': images_files,
        'documents': documents_files,
        'audio': audio_files,
        'video': video_files,
        'archives': archives_files,
        'other': other
    }

    for file_type, files in file_types.items():
        for file in files:
            if file_type == 'archives':
                handle_archive(file, folder_path, file_type)
            else:
                handle_file(file, folder_path, file_type)

    remove_empty_folders(folder_path)

    # Rest of the code remains unchanged
    print("Contents of Organized Folders:")
    for item in folder_path.iterdir():
        if item.is_dir():
            print(f"Folder: {item}")
            for subitem in item.iterdir():
                print(f"  {subitem}")
        else:
            print(f"File: {item}")
    print(f'images: {[normalize(file.name) for file in images_files]}')
    print(f'video: {[normalize(file.name) for file in video_files]}')
    print(f'documents: {[normalize(file.name) for file in documents_files]}')
    print(f'audio: {[normalize(file.name) for file in audio_files]}')
    print(f'archives: {[normalize(file.name) for file in archives_files]}')
    print(f"other: {[normalize(file.name) for file in other]}")
    print(f"unknowns extensions: {[normalize(ext) for ext in unknown]}")
    print(f"unique extensions: {[normalize(ext) for ext in extensions]}")


@input_error
def func_help():
    return ('Hi! If you want to start working, just enter "hello"\n' +
            'Number phone in 10 numbers, for example 0001230001\n' +
            'The representation of all commands looks as follows:\n' +
            '"hello" - start work with bot\n' +
            '"add contact" name phone1 phone2 ...\n' +
            '"add email" name example@mail.com ...\n' +
            '"add adr" name West 141 st. ...\n' +
            '"add brd" name 15.12.1990 ...\n' +
            '"change" name old_phone new_phone\n' +
            '"change_info" name atribute(phone,birthday,email) old_atribute new_atribut\n' +
            '"delete_info" - name atribute(phone,birthday,email)\n' +
            '"phone" name or phone number\n' +
            '"show all" - for show all information\n' +
            '"good bye", "close", "exit" - for end work\n' +
            '"delete" - delete info of name\n' +
            '"search" - command for search. Just enter "search" and something about contact like name or phone\n' +
            '"sort" - way to path\n' +
            '"search by tag" - enter tag\n' +
            '"create note" - title content\n' +
            '"show note" - just show all notes\n' +
            '"edit note" - note_index_str and new_content\n' +
            '"remove note" - note_index_str\n' +
            '"help" - get help for commands\n' +
            '"close, exit, good bye" - for quit from bot')


COMMANDS = {
    "Hello": func_hello,
    "Add Contact ": func_add_name_phones,
    "Change ": func_change,
    "Phone ": func_search,
    "Show All": func_show_all,
    "Delete ": func_delete,
    "Search By Tag": search_by_tag,
    "Add Email ": func_add_email,
    "Add Adr ": func_add_address,
    "Add brd ": func_add_birthday,
    "Change_Info": func_change_info,
    "Delete_Info": func_delete_info,
    "Search ": func_search_contacts,
    "Sort ": do_sort_folder,
    "Create Note": add_note,
    "Show Notes": view_notes,
    "Edit Note": edit_note,
    "Remove Note": remove_note,
    "Help": func_help,
    "Close": func_exit,
    "Exit": func_exit,
    "Good Bye": func_exit
}
address_book = AddressBook()
atexit.register(address_book.save_notes)

command_completer = WordCompleter(COMMANDS, ignore_case=True)


def main():
    # load data from disk if data is available
    address_book.load_data_from_disk()
    address_book.load_notes()

    while True:

        # user_input = input('Please, enter the valid command: ')
        # ЗАПУСКАЙТЕ ЧЕРЕЗ TERMINAL: python maim.py
        # АБО відкоментуйте рядок вище, закоментуйте нижче для виключення prompt та запуску в IDLE
        user_input = prompt("Please, enter the valid command: ", completer=command_completer)

        if user_input.lower() in ["exit", "close", "good bye"]:
            print(func_exit())
            break
        else:
            handler, arguments = parser(user_input)
            print(handler(*arguments))


def convector_to_dictionary(address_book):
    data = {}
    for rec in address_book.values():
        data.update(
            {str(rec.name):
                {
                    "phones": str(rec.phones),
                    "email": str(rec.email),
                    "birthday": str(rec.birthday),
                    "address": str(rec.address)
                }
            }
        )
    return data


test_contact = convector_to_dictionary(address_book)

page_number = 0


def main_ui():  # Определяем функцию main
    address_book = AddressBook()
    address_book.load_data_from_disk()

    pygame.init()  # Инициализируем Pygame
    screen = pygame.display.set_mode((800, 583))  # Создаем экран размером 800x600 пикселей
    font = pygame.font.Font(None, 36)  # Загружаем шрифт размером 36
    text = ''  # Инициализируем переменную для хранения введенного текста
    input_rect = pygame.Rect(0, 32, 140, 32)  # Создаем прямоугольник для поля ввода текста
    show_all_rect = pygame.Rect(0, 0, 150, 32)
    prev_page_rect = pygame.Rect(0, 0, 140, 32)
    next_page_rect = pygame.Rect(141, 0, 140, 32)
    hit_box_rect_1 = pygame.Rect(0, 30, 1000, 24)
    hit_box_rect_2 = pygame.Rect(0, 56, 1000, 24)
    hit_box_rect_3 = pygame.Rect(0, 82, 1000, 24)
    hit_box_rect_4 = pygame.Rect(0, 108, 1000, 24)
    hit_box_rect_5 = pygame.Rect(0, 134, 1000, 24)
    hit_box_rect_6 = pygame.Rect(0, 160, 1000, 24)
    hit_box_rect_7 = pygame.Rect(0, 185, 1000, 24)
    hit_box_rect_8 = pygame.Rect(0, 210, 1000, 24)
    hit_box_rect_9 = pygame.Rect(0, 234, 1000, 24)
    hit_box_rect_10 = pygame.Rect(0, 260, 1000, 24)
    hit_box_rect_11 = pygame.Rect(0, 285, 1000, 24)
    hit_box_rect_12 = pygame.Rect(0, 310, 1000, 24)
    hit_box_rect_13 = pygame.Rect(0, 335, 1000, 24)
    hit_box_rect_14 = pygame.Rect(0, 360, 1000, 24)
    hit_box_rect_15 = pygame.Rect(0, 383, 1000, 24)
    hit_box_rect_16 = pygame.Rect(0, 408, 1000, 24)
    hit_box_rect_17 = pygame.Rect(0, 432, 1000, 24)
    hit_box_rect_18 = pygame.Rect(0, 456, 1000, 24)
    hit_box_rect_19 = pygame.Rect(0, 480, 1000, 24)
    hit_box_rect_20 = pygame.Rect(0, 504, 1000, 24)
    hit_box_rect_21 = pygame.Rect(0, 532, 1000, 24)
    hit_box_rect_22 = pygame.Rect(0, 559, 1000, 24)

    hit_box_rect_1_ = pygame.Rect(0, 30, 1000, 24)
    hit_box_rect_2_ = pygame.Rect(0, 60, 1000, 24)
    hit_box_rect_3_ = pygame.Rect(0, 82, 1000, 24)
    hit_box_rect_4_ = pygame.Rect(0, 104, 1000, 24)
    hit_box_rect_5_ = pygame.Rect(0, 126, 1000, 24)
    hit_box_rect_6_ = pygame.Rect(0, 148, 1000, 24)
    hit_box_rect_7_ = pygame.Rect(0, 170, 1000, 24)
    hit_box_rect_8_ = pygame.Rect(0, 192, 1000, 24)
    hit_box_rect_9_ = pygame.Rect(0, 214, 1000, 24)
    hit_box_rect_10_ = pygame.Rect(0, 236, 1000, 24)
    hit_box_rect_11_ = pygame.Rect(0, 258, 1000, 24)
    hit_box_rect_12_ = pygame.Rect(0, 281, 1000, 24)
    hit_box_rect_13_ = pygame.Rect(0, 303, 1000, 24)
    hit_box_rect_14_ = pygame.Rect(0, 325, 1000, 24)
    hit_box_rect_15_ = pygame.Rect(0, 349, 1000, 24)
    hit_box_rect_16_ = pygame.Rect(0, 371, 1000, 24)
    hit_box_rect_17_ = pygame.Rect(0, 393, 1000, 24)
    hit_box_rect_18_ = pygame.Rect(0, 415, 1000, 24)
    hit_box_rect_19_ = pygame.Rect(0, 437, 1000, 24)
    hit_box_rect_20_ = pygame.Rect(0, 459, 1000, 24)
    hit_box_rect_21_ = pygame.Rect(0, 481, 1000, 24)
    hit_box_rect_22_ = pygame.Rect(0, 503, 1000, 24)
    hit_box_rect_23_ = pygame.Rect(0, 525, 1000, 24)
    hit_box_rect_24_ = pygame.Rect(0, 547, 1000, 24)
    back_button_rect_to_scr_1 = pygame.Rect(282, 0, 60, 32)
    back_button_rect_to_scr_2 = pygame.Rect(2, 499, 60, 32)

    color_active = pygame.Color('dodgerblue2')  # Задаем цвет для активного состояния поля ввода
    color_inactive = pygame.Color('lightskyblue3')  # Задаем цвет для неактивного состояния поля ввода
    color = color_inactive  # Инициализируем текущий цвет поля ввода
    active = False  # Флаг активности поля ввода

    my_font = pygame.font.SysFont("Comic Sans MS", 18)
    show_all = my_font.render("Show all contacts", True, 'black')
    next_page = my_font.render("Next page", True, 'black')
    prev_page = my_font.render("Previous page", True, 'black')
    back_button_to_scr_1 = my_font.render("Back", True, 'black')
    back_button_to_scr_2 = my_font.render("Back", True, 'black')

    page_number = 0

    def sorterrer(test_contact, counter_in):
        global empty
        empty = True
        ret_dict = {}
        counter_out = counter_in + 22
        counter = 0
        counter_for_empty = 0
        for key, value in test_contact.items():
            if counter >= counter_in and counter <= (counter_out - 1):
                counter_for_empty += 1
                ret_dict[key] = value
                counter_in += 1
            counter += 1
        if counter_for_empty < 22:
            empty = False
        return ret_dict

    def contact_render(dict_of_contacts, pos_y, pos_x):
        for key, value_dict in dict_of_contacts.items():

            ret = ''
            pos_y += 25
            ret += key + " "
            for key, value in value_dict.items():
                ret += key + ' ' + value + ' '
            text_for_contact_pr = my_font.render(ret, True, 'black')
            screen.blit(text_for_contact_pr, ((pos_x), (pos_y + 20)))

    def func_search_contacts(*args):
        query = args[0]
        matching_contacts = address_book.search_contact(query)

        if matching_contacts:
            result = []
            result += (str(record.name) for record in matching_contacts)
            return result
        return ''

    screens = 1
    running = True
    counter_navigation = page_number
    while running:  # Запускаем бесконечный цикл обработки событий

        pos_y = -13
        pos_x = 0
        screen.fill((255, 255, 255))  # Заполняем экран цветом

        if screens == 1:
            search_counter = 0
            for event in pygame.event.get():  # Перебираем все события в очереди
                if event.type == pygame.QUIT:  # Если событие - выход из программы
                    pygame.quit()  # Выходим из Pygame
                    sys.exit()  # Завершаем программу
                if event.type == pygame.MOUSEBUTTONDOWN:  # Если нажата кнопка мыши
                    if input_rect.collidepoint(event.pos):  # Если позиция щелчка находится в пределах поля ввода
                        active = not active  # Инвертируем флаг активности поля ввода
                    else:
                        active = False  # В противном случае сбрасываем флаг активности поля ввода
                    color = color_active if active else color_inactive  # Устанавливаем цвет в зависимости от активности
                if event.type == pygame.KEYDOWN:  # Если нажата клавиша
                    if active:  # Если поле ввода активно
                        if event.key == pygame.K_RETURN:  # Если нажата клавиша Enter
                            print(text)  # Выводим введенный текст
                            text = ''  # Сбрасываем текст после нажатия Enter
                        elif event.key == pygame.K_BACKSPACE:  # Если нажата клавиша Backspace
                            text = text[:-1]  # Удаляем последний символ из текста
                        else:
                            text += event.unicode  # Добавляем символ введенный пользователем в текст
                if event.type == pygame.MOUSEBUTTONDOWN:  # Если нажата кнопка мыши
                    if show_all_rect.collidepoint(event.pos):  # Если позиция щелчка находится в пределах поля ввода
                        prev_sreens = screens
                        screens = 2
                if len(func_search_contacts(text)) > 0:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if hit_box_rect_2_.collidepoint(event.pos):
                            search_counter = 1
                if len(func_search_contacts(text)) > 1:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if hit_box_rect_3_.collidepoint(event.pos):
                            search_counter = 2
                if len(func_search_contacts(text)) > 2:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if hit_box_rect_4_.collidepoint(event.pos):
                            search_counter = 3
                if len(func_search_contacts(text)) > 3:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if hit_box_rect_5_.collidepoint(event.pos):
                            search_counter = 4
                if len(func_search_contacts(text)) > 4:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if hit_box_rect_6_.collidepoint(event.pos):
                            search_counter = 5
                if len(func_search_contacts(text)) > 5:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if hit_box_rect_7_.collidepoint(event.pos):
                            search_counter = 6
                if len(func_search_contacts(text)) > 6:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if hit_box_rect_8_.collidepoint(event.pos):
                            search_counter = 7

                if len(func_search_contacts(text)) > 7:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if hit_box_rect_9_.collidepoint(event.pos):
                            search_counter = 8
                if len(func_search_contacts(text)) > 8:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if hit_box_rect_10_.collidepoint(event.pos):
                            search_counter = 9
                if len(func_search_contacts(text)) > 9:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if hit_box_rect_11_.collidepoint(event.pos):
                            search_counter = 10
                if len(func_search_contacts(text)) > 10:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if hit_box_rect_12_.collidepoint(event.pos):
                            search_counter = 11
                if len(func_search_contacts(text)) > 11:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if hit_box_rect_13_.collidepoint(event.pos):
                            search_counter = 12
                if len(func_search_contacts(text)) > 12:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if hit_box_rect_14_.collidepoint(event.pos):
                            search_counter = 13
                if len(func_search_contacts(text)) > 13:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if hit_box_rect_15_.collidepoint(event.pos):
                            search_counter = 14
                if len(func_search_contacts(text)) > 14:
                    if event.type == pygame.MOUSEBUTTONDOWN:  # ��сли нажата к
                        if hit_box_rect_16_.collidepoint(event.pos):
                            search_counter = 15
                if len(func_search_contacts(text)) > 15:
                    if event.type == pygame.MOUSEBUTTONDOWN:  # ��сли нажата к
                        if hit_box_rect_17_.collidepoint(event.pos):
                            search_counter = 16
                if len(func_search_contacts(text)) > 16:
                    if event.type == pygame.MOUSEBUTTONDOWN:  # ��сли нажата к
                        if hit_box_rect_18_.collidepoint(event.pos):
                            search_counter = 17
                if len(func_search_contacts(text)) > 17:
                    if event.type == pygame.MOUSEBUTTONDOWN:  # ��сли нажата к
                        if hit_box_rect_19_.collidepoint(event.pos):
                            search_counter = 18
                if len(func_search_contacts(text)) > 18:
                    if event.type == pygame.MOUSEBUTTONDOWN:  # ��сли нажата к
                        if hit_box_rect_20_.collidepoint(event.pos):
                            search_counter = 19
                    if event.type == pygame.MOUSEBUTTONDOWN:  # ��сли нажата к
                        if hit_box_rect_21_.collidepoint(event.pos):
                            search_counter = 20
                    if event.type == pygame.MOUSEBUTTONDOWN:  # ��сли нажата к
                        if hit_box_rect_22_.collidepoint(event.pos):
                            search_counter = 21
                    if event.type == pygame.MOUSEBUTTONDOWN:  # ��сли нажата к
                        if hit_box_rect_23_.collidepoint(event.pos):
                            search_counter = 22
                    if event.type == pygame.MOUSEBUTTONDOWN:  # ��сли нажата к
                        if hit_box_rect_24_.collidepoint(event.pos):
                            search_counter = 23

            if search_counter > 0:
                in_counter = 0
                counter_navigation = 0
                for key in test_contact:
                    in_counter += 1
                    if key == func_search_contacts(text)[search_counter - 1]:
                        counter_navigation = in_counter
                prev_sreens = screens
                screens = 3
            if text:
                if func_search_contacts(text) != None:
                    pos_y = 60
                    for el in func_search_contacts(text):
                        show_name_of_match_c = my_font.render(str(el), True, 'black')
                        screen.blit(show_name_of_match_c, (3, pos_y))
                        pos_y += 22

            pygame.draw.rect(screen, color, input_rect, 2)  # Рисуем прямоугольник поля ввода
            text_surface = font.render(text, True, (0, 0, 0))  # Рендерим текст
            screen.blit(text_surface, (input_rect.x + 5, input_rect.y + 5))  # Отображаем текст на экране
            input_rect.w = max(200, text_surface.get_width() + 10)  # Устанавливаем ширину поля ввода

            screen.blit(show_all, (3, 3))
            pygame.draw.rect(screen, 'black', show_all_rect, 2)  # рисуем кнопку для show all
        if screens == 2:

            for event in pygame.event.get():  # Перебираем все события в очереди
                if event.type == pygame.QUIT:  # Если событие - выход из программы
                    pygame.quit()  # Выходим из Pygame
                    sys.exit()  # Завершаем программу
                if event.type == pygame.MOUSEBUTTONDOWN:  # Если нажата кнопка мыши
                    if prev_page_rect.collidepoint(event.pos):
                        if page_number > 0:
                            page_number -= 22
                            counter_navigation = page_number
                if event.type == pygame.MOUSEBUTTONDOWN:  # Если нажата кнопка мыши
                    if next_page_rect.collidepoint(event.pos):  # Если позиция щелчка находится в пределах поля ввода
                        if empty:
                            page_number += 22
                            counter_navigation = page_number

                if event.type == pygame.MOUSEBUTTONDOWN:  # Если нажата кнопка мыши
                    if back_button_rect_to_scr_1.collidepoint(event.pos):
                        prev_sreens = screens
                        screens = 1

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hit_box_rect_1.collidepoint(event.pos):
                        counter_navigation += 1
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hit_box_rect_2.collidepoint(event.pos):
                        counter_navigation += 2
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hit_box_rect_3.collidepoint(event.pos):
                        counter_navigation += 3
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hit_box_rect_4.collidepoint(event.pos):
                        counter_navigation += 4
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hit_box_rect_5.collidepoint(event.pos):
                        counter_navigation += 5
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hit_box_rect_6.collidepoint(event.pos):
                        counter_navigation += 6
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hit_box_rect_7.collidepoint(event.pos):
                        counter_navigation += 7
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hit_box_rect_8.collidepoint(event.pos):
                        counter_navigation += 8
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hit_box_rect_9.collidepoint(event.pos):
                        counter_navigation += 9
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hit_box_rect_10.collidepoint(event.pos):
                        counter_navigation += 10
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hit_box_rect_11.collidepoint(event.pos):
                        counter_navigation += 11
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hit_box_rect_12.collidepoint(event.pos):
                        counter_navigation += 12
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hit_box_rect_13.collidepoint(event.pos):
                        counter_navigation += 13
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hit_box_rect_14.collidepoint(event.pos):
                        counter_navigation += 14
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hit_box_rect_15.collidepoint(event.pos):
                        counter_navigation += 15
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hit_box_rect_16.collidepoint(event.pos):
                        counter_navigation += 16
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hit_box_rect_17.collidepoint(event.pos):
                        counter_navigation += 17
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hit_box_rect_18.collidepoint(event.pos):
                        counter_navigation += 18
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hit_box_rect_19.collidepoint(event.pos):
                        counter_navigation += 19
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hit_box_rect_20.collidepoint(event.pos):
                        counter_navigation += 20
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hit_box_rect_21.collidepoint(event.pos):
                        counter_navigation += 21
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hit_box_rect_22.collidepoint(event.pos):
                        counter_navigation += 22
            if counter_navigation > page_number:
                prev_sreens = screens
                screens = 3
            else:
                counter_navigation = page_number

            screen.blit(prev_page, (10, 3))
            screen.blit(next_page, (160, 3))
            screen.blit(back_button_to_scr_1, (290, 3))
            pygame.draw.rect(screen, 'black', prev_page_rect, 2)  # рисуем кнопку для show all
            pygame.draw.rect(screen, 'black', next_page_rect, 2)
            pygame.draw.rect(screen, 'black', back_button_rect_to_scr_1, 2)
            contact_render(sorterrer(test_contact, page_number), pos_y, pos_x)

        if screens == 3:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if back_button_rect_to_scr_2.collidepoint(event.pos):
                        counter_navigation = page_number

                        screens = prev_sreens

            c = 0
            for cont_name, cont_info in test_contact.items():
                c += 1
                pos_y = 10
                if c == counter_navigation:
                    for key, value in cont_info.items():
                        if c == counter_navigation:
                            pos_y += 40
                            show_c_key = my_font.render(str(key), True, 'black')
                            screen.blit(show_c_key, (3, pos_y))
                            show_c_info = my_font.render(str(value), True, 'black')
                            screen.blit(show_c_info, ((len(str(key)) * 11.5), pos_y))

                if c == counter_navigation:
                    show_name = my_font.render(cont_name, True, 'black')
                    screen.blit(show_name, (3, 3))

            screen.blit(back_button_to_scr_2, (10, 500))
            pygame.draw.rect(screen, 'black', back_button_rect_to_scr_2, 2)

        pygame.display.flip()  # Обновляем экран


address_book.save_data_to_disk()

if __name__ == '__main__':  # Если файл запущен напрямую

    arguments = sys.argv[1:]
    if len(sys.argv) > 1:
        if sys.argv[1] == "ui":
            main_ui()
    else:
        main()  # Вызываем функцию main()
