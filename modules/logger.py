from datetime import datetime
import traceback


DELIMITER = "#####################################"
FLAG_ERROR = "ERRO"
FLAG_INFO = "INFO"
FLAG_COMMAND = "CMD"
FLAG_LINK = "LINK"
FLAG_LENGTH = 4


def date_format(date: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
	"""
	%Y  -  Year (YYYY)
	%m  -  Month (mm)
	%d  -  Day (dd)
	%H  -  Hour (hh)
	%M  -  Minute (MM)
	%S  -  Second (ss)
	"""
	return format.replace("\\%", "\0") \
				.replace("%Y", "{:0>4}".format(date.year)) \
				.replace("%m", "{:0>2}".format(date.month)) \
				.replace("%d", "{:0>2}".format(date.day)) \
				.replace("%H", "{:0>2}".format(date.hour)) \
				.replace("%M", "{:0>2}".format(date.minute)) \
				.replace("%S", "{:0>2}".format(date.second)) \
				.replace("\0", "%")


def log(*messages: str, flag: str = FLAG_INFO):
	date = date_format(datetime.now())
	flag = "" if flag is None else " - {: <{len}}".format(flag, len=FLAG_LENGTH)
	if len(messages) == 0:
		messages = "",
	for line in messages:
		print(f"[{date}{flag}]:  {line}")


def log_embed(*messages: str, flag: str = FLAG_INFO,
			  before: list[str] = [""], after: list[str] = []):
	log(*before, DELIMITER, *messages, DELIMITER, *after, flag=flag)


def log_exception(exception: Exception, *messages: str, print_stack_trace: bool = True,
				  before: list[str] = ["", ""], after: list[str] = [""]):
	log(
		*before,
		DELIMITER,
		f"[Exception occured] {exception.__class__.__name__}: '{exception}'.",
		*messages, *([""] if print_stack_trace else []),
		flag=FLAG_ERROR
	)
	if print_stack_trace:
		traceback.print_exc()
	log(DELIMITER, *after, flag=FLAG_ERROR)
