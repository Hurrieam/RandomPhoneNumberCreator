import random
import os

os.system("title 手机号码随机生成器 版权所有 快速的飓风. © 2020")
os.system("color F0")

beginner = ['134', '135', '136', '137', '138', '139', '147', '150', '151', '152', '157', '158', '159', '182', '187', '188', '130', '131', '132', '155', '156', '185', '186', '133', '153', '180', '189']

while True:

    count = input("请输入需要的手机号码个数\n>>")

    if count.isdigit():

        print("\n")

        for i in range(0, int(count), 1):
            print("[" + str(i + 1) + "] " + beginner[random.randint(0, 26)], end = "")

            for j in range(0, 8, 1):
                print(random.randint(0, 9), end = "")

            print("\n")
        print("生成完毕！")

        while True:

            choice = str(input("是否继续使用？\n[Y] 是\n[N] 否\n>>"))
            if choice == "y" or choice == "Y":
                print("\n")
                break
            if choice == "n" or choice == "N":
                print("\n")
                print("感谢使用，再见！")
                input()
                exit(0)
            else:
                print("您的输入有误，请检查后重新输入！")
                continue

    else:
        print("您的输入有误，请检查后重新输入！")
        continue
