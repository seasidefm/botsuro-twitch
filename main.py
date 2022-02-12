from dotenv import load_dotenv
from bot import Bot

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print("Starting bot ->")
    load_dotenv()

    bot = Bot()
    bot.run()
