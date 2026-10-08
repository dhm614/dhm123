import random
from datetime import datetime
from pathlib import Path


SCORE_FILE = Path(__file__).with_name("scores.txt")


def save_score(result, attempts):
    record = f"{datetime.now():%Y-%m-%d %H:%M:%S}\t{result}\t{attempts}\n"
    with SCORE_FILE.open("a", encoding="utf-8") as file:
        file.write(record)


def show_scores():
    if not SCORE_FILE.exists():
        print("暂无获胜记录。")
        return

    records = [line.split("\t") for line in SCORE_FILE.read_text(encoding="utf-8").splitlines()]
    wins = [(date_time, int(attempts)) for date_time, result, attempts in records if result == "胜"]
    wins.sort(key=lambda record: record[1])

    if not wins:
        print("暂无获胜记录。")
        return

    print("历史最少次数前 5 名：")
    for rank, (date_time, attempts) in enumerate(wins[:5], 1):
        print(f"{rank}. {date_time} - {attempts} 次")


def play_game():
    answer = random.randint(1, 100)
    attempts = 0

    print("我想好了一个 1~100 的整数。")

    while attempts < 7:
        try:
            guess = int(input("请输入你的猜测："))
        except ValueError:
            print("请输入 1~100 之间的整数")
            continue

        if not 1 <= guess <= 100:
            print("请输入 1~100 之间的整数")
            continue

        attempts += 1

        if guess < answer:
            print("小了。")
        elif guess > answer:
            print("大了。")
        else:
            print(f"猜对了！你一共猜了 {attempts} 次。")
            return "胜", attempts

    print(f"7 次机会用完了，答案是 {answer}。")
    return "负", attempts


def main():
    while True:
        result, attempts = play_game()
        save_score(result, attempts)

        again = input("输入 y 再来一局，输入 h 查看排行榜，其他输入退出：").strip()
        while again == "h":
            show_scores()
            again = input("输入 y 再来一局，输入 h 查看排行榜，其他输入退出：").strip()

        if again != "y":
            print("游戏结束。")
            break


if __name__ == "__main__":
    main()
