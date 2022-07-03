from datetime import datetime


def logger(massage: str, write_file: str = 'image_backup_logger.log') -> None:
    with open(write_file, 'a') as file:
        file.write(f'{datetime.now()}: {massage}\n')
