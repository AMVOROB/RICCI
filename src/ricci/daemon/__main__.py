import traceback

from .main import main

if __name__ == "__main__":
    try:
        main()
    except BaseException:
        # ядро не должно умирать молча: пишем трейс всегда
        with open(r"D:\Projects\RICCI\logs\daemon.crash.log", "a",
                  encoding="utf-8") as f:
            f.write(traceback.format_exc() + "\n")
        raise