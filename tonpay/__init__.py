import json
from loguru import logger
import sys

_config = {}
with open("config.json", "r") as config_file:
    _config = json.loads(config_file.read())
    
# defining loggers 
fmt = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "cid: {extra[chat_id]} - <level>{message}</level>"
)
logger.configure(extra={"chat_id": ""})  # Default values
logger.remove(None) # removing all loggers
isprod: bool = config["general"].get("isprod", False)
diagnose = False if isprod else True
logger.add("logs/errors_{time:YYYY-MM-DD_HH:mm:ss}.log", level="ERROR",
           diagnose=diagnose, backtrace=True,
           enqueue=True, rotation="500 MB", format=fmt)
log_level: str = config["general"].get("log_level", "INFO").upper()
sink = f"logs/{log_level.lower()}_" + "{time:YYYY-MM-DD_HH:mm:ss}.log"
logger.add(sink, level=log_level, 
           diagnose=diagnose, backtrace=False, 
           enqueue=True, rotation="500 MB")
logger.add("logs/telegram_{time:YYYY-MM-DD_HH:mm:ss}.log", level=log_level,
           diagnose=diagnose, backtrace=True, 
           filter= lambda rec: "chat_id" in rec["extra"] and rec["extra"]["chat_id"] != "")
logger.add(sys.stdout, level=log_level,
           diagnose=diagnose, backtrace=True, format=fmt)

# initial logging 
logger.info("app started")
logger.info("general configurations: {conf}", conf = config["general"])
logger.info("logs with log level {level} will be saved at {sink}", 
            level=log_level, sink=sink)
