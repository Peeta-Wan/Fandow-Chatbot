import json
import os
import re
import shutil
import time
import random

import pandas as pd
import tiktoken


def chat_return_tokens(model: str, messages: list):
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo-0301":  # note: future models may deviate from this
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\\n{content}<im_end>\\n
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not presently implemented for model {model}.See <https://github.com
            /openai/openai-python/blob/main/chatml.md> for information on how messages are converted to tokens.""")


def tojsonl(excel, file, prompt, replace_1, file_name, root_url, is_sort=False):
    pf = pd.read_excel(excel)
    # prompt_dict = {
    #     "role": "system",
    #     "content": prompt
    # }

    if is_sort:
        pf = pf.sort_index(ascending=False)
    # print(pf.values)

    josnl_list = []
    # 图片赋值
    # r = "用户发送图片"
    # g = "症状："
    # s = "性别"
    # p = ""
    # prout = ""
    # # 给图片加内容
    # for pfvalues in pf.values:
    #     if "闭合性粉刺" in str(pfvalues[1]):
    #         g = "症状：闭合性粉刺"
    #         break
    #     elif "丘疹型痘痘" in str(pfvalues[1]):
    #         g = "症状：丘疹型痘痘"
    #         break
    #     elif "聚合型痘痘" in str(pfvalues[1]):
    #         g = "症状：聚合型痘痘"
    #         break
    #     else:
    #         g = "症状：炎症痘痘"
    for pfvaluse1 in pf.values:
        # print(">>>>"*10,str(pfvaluse1[1]))
        if "系统提示:粉丝成功支付订单" in str(pfvaluse1[1]):
            if "男" in str(pfvaluse1[1]):
                s = "性别男"
                break
            else:
                s = "性别女"
                break

        if re.search('{"title":"【(.*?)】', str(pfvaluse1[1])) is None:
            if re.search('{"description":"【(.*?)】",', str(pfvaluse1[1])) is None:
                continue
            else:
                a = re.findall('{"description":"【(.*?)】",', str(pfvaluse1[1]))[0]
                if "男" in a:
                    s = "性别男"
                    prout = replace_1 + a
                    break
                else:
                    s = "性别女"
                    prout = replace_1 + a
                    break
        else:
            a = re.findall('{"title":"【(.*?)】', str(pfvaluse1[1]))[0]
            if "男" in a:
                s = "性别男"
                prout = replace_1 + a
                break
            else:
                s = "性别女"
                prout = replace_1 + a
                break

    # 判断有没有粉丝接待，如果有，改成  系统提示：用户点击了菜单：我要找小希
    try:
        pf.loc[pf['content'].str.contains("关注，现在分配给你，请做接待。", na=False), "content"] = "系统提示：用户点击了菜单：我要找小希"
    except:
        print(file)
    # 已转接人工咨询，你好，我是IRY9年专业护肤顾问小希老师 改成  系统提示：用户点击了菜单：我要找小希
    pf.loc[pf['content'].str.contains("已转接人工咨询，你好，我是", na=False), "content"] = "系统提示：用户点击了菜单：我要找小希"

    # pf.loc[
    #     pf['content'].str.contains("/public/chat/upload/", na=False), "content"] = r + ',' + s + ',' + g + ',' + prout

    if os.path.exists(root_url + "/" + prout) is False:
        try:
            os.mkdir(root_url + "/" + prout)
        except OSError:
            os.mkdir(root_url + "/" + "其他产品")

    # 链接初始化

    # 推荐用户图片
    pf.loc[pf['content'].str.contains("http://crm-chat", na=False), "content"] = "vxpic"

    # 推送优惠卷
    pf.loc[pf['content'].str.contains("https://crm.wqc.so/shop/User/usercoupon/", na=False), "content"] = "推送优惠券"

    # 新用户优惠卷
    pf.loc[pf['content'].str.contains("http://crm.wqc.so/shop/user/getcoupon/", na=False), "content"] = "推送新用户优惠券"

    # 修改评价
    pf.loc[pf['content'].str.contains("https://crm.wqc.so/shop/custom/evaluate", na=False), "content"] = "评价链接"

    # 问卷链接
    pf.loc[pf['content'].str.contains("https://crm.wqc.so/shop/FansSignin/userInfo/", na=False), "content"] = "问卷链接"

    # 申请链接
    pf.loc[
        pf['content'].str.contains("http://crm.wqc.so/shop/User/queryOrders/template/", na=False), "content"] = "申请链接"

    # 下单支付
    pf.loc[pf['content'].str.contains("http://crm.wqc.so/shop/pay/payment", na=False), "content"] = "支付下单链接"

    # 抽奖链接
    pf.loc[pf['content'].str.contains("http://crm.wqc.so/shop/rollCardActivity", na=False), "content"] = "抽奖链接"

    # 药监局链接
    pf.loc[pf['content'].str.contains("https://hzpba.nmpa.gov.cn/gccx/", na=False), "content"] = "药监局链接"

    # 不知道什么的链接 ,默认产品链接  http://crm.wqc.so/shop/Default/querygoods/id/13250/token/5aec4ee6b1c66/customid/1141.html
    # ?1680791467
    pf.loc[pf['content'].str.contains("http://crm.wqc.so/shop/Default/querygoods/", na=False), "content"] = "产品链接"

    # 投诉链接
    pf.loc[pf['content'].str.contains("https://crm.wqc.so/shop/complaint/", na=False), "content"] = "投诉链接"

    # 待支付链接
    pf.loc[pf['content'].str.contains("https://crm.wqc.so/shop/User/index/template/", na=False), "content"] = "待支付链接"

    # 确认订单链接
    pf.loc[pf['content'].str.contains("http://crm.wqc.so/shop/default/orderIrm/", na=False), "content"] = "确认订单链接"

    # 角色转换
    pf.loc[pf["send"] == 'customer', "send"] = 'assistant'

    pf_init = pf.loc[:, ["content", "send", "created_time", "content_type"]]

    my_dict = open(file_name, "a", encoding='utf-8')
    # josnl_list.append(prompt_dict)
    a = ""
    b = ""
    pf_list = pf_init.values
    # print(pf_list[0])

    for i in range(0, len(pf_list)):
        # if p == prout:
        #     break
        if pf_list[i][1] == "user":
            # print("未处理", pf_list[i][0])
            if a != str(pf_list[i][0]) and "系统提示:粉丝成功支付订单" not in b:
                # print("已经处理", pf_list[i][0])
                # if "关注，现在分配给你，请做好接待。" in str(pf_list[i][0]):
                #     user_content = "系统提示：粉丝关注，现在分配给你，请做好接待。"
                # else:
                #     user_content = str(pf_list[i][0])
                josnl_list.append(
                    {
                        "role": "user",
                        "content": "content[%s]\nsendtime[%s]" % (
                            pf_list[i][0] if "系统提示:粉丝成功支付订单" not in str(
                                pf_list[i][0]) else "粉丝成功支付订单",
                            pf_list[i][2]
                        )
                    }
                )
                # 并给a赋值
                a = "系统提示：用户点击了菜单：我要找小希"
                b = str(pf_list[i][0])
                # if "http" in str(pf_list[i][0]):
                #     print(str(pf_list[i][0]))

        elif pf_list[i][1] == "assistant" and pf_list[i - 1][1] == 'user':
            # 用户时间
            # user_time = pf_list[i-1][2]
            try:
                user_time = time.strptime(pf_list[i - 1][2], "%Y-%m-%d %H:%M:%S")
            except TypeError:
                user_time = time.strptime(str(pf_list[i - 1][2]), "%Y-%m-%d %H:%M:%S")
            user_tamp = time.mktime(user_time)
            count = 0
            c1 = ""

            try:
                while pf_list[i + count][1] == "assistant":
                    count = count + 1
            except IndexError:
                count = count + 1

            count1 = i + count if (i + count) <= len(pf_list) else len(pf_list)
            for j in range(i, count1):
                # print("数字", j)
                next_role = pf_list[j + 1][1] if j != (len(pf_list) - 1) else pf_list[j][1]
                # recoverytime = pf_list[j][2]

                try:
                    recoverytime = time.strptime(pf_list[j][2], "%Y-%m-%d %H:%M:%S")
                except:
                    recoverytime = time.strptime(str(pf_list[j][2]), "%Y-%m-%d %H:%M:%S")
                recoverytamp = time.mktime(recoverytime)
                waitingtime = int(recoverytamp - user_tamp)

                if '{"title":' in str(pf_list[j][0]):
                    content11 = replace_1 + re.findall('{"title":"【(.*?)】",', pf_list[j][0])[0]
                    p = prout
                elif '{"description":' in str(pf_list[j][0]):
                    content11 = replace_1 + re.findall('{"description":"【(.*?)】",', pf_list[j][0])[0]
                    p = prout
                elif "收货人姓名" in str(pf_list[j][0]):
                    # 转换成收件人信息的英文
                    content11 = "【请核对收货信息】"
                # elif "系统提示：粉丝成功支付了" in str(pf_list[j][0]):
                #     content11 = "粉丝成功支付"
                else:
                    content11 = str(pf_list[j][0])

                c1 = c1 + "round-%s\ncontent[%s]\nevent[%s]\nrecoverytime[%s]\nwaitingtime[" \
                          "%s]\nwaitingtimeout-strategy[%s]\n" % (
                         str(j - i + 1),
                         content11,
                         pf_list[j][3],
                         pf_list[j][2],
                         str(waitingtime),
                         "waiting for user" if next_role == 'user' else "assistant again"
                     )
            content = "replies-round-strategy:" + str(count) + "\n" + c1

            if content[-17:] == "[assistant again]":
                content = content[:-17] + "[waiting for user]"

            josnl_list.append(
                {
                    "role": "assistant",
                    "content": content
                }
            )
        else:
            continue
    # print(josnl_list)

    if 2 < chat_return_tokens("gpt-3.5-turbo-0301", josnl_list) <= 16385:
        # print(josnl_list)
        # print(chat_return_tokens("gpt-3.5-turbo-0301", josnl_list), "！！！！" * 10, excel)
        jsonl = json.dumps({"messages": josnl_list}, ensure_ascii=False)

        my_dict.write(jsonl + "\n")
        #
        # shutil.copy(
        #     excel_file,
        #     root_url + "/" + prout + '/' + file
        # )
    else:
        # shutil.move(
        #     excel, "D:/Reptile_fandow/微调/maxtoken/" + file
        # )
        print(josnl_list)
        print(chat_return_tokens("gpt-3.5-turbo-0301", josnl_list), "-" * 10, excel)
        # if os.path.exists(root_url + "/" + "聊天没推荐就支付了") is False:
        #     os.mkdir(root_url + "/" + "聊天没推荐就支付了")
        # shutil.copy(
        #     excel_file,
        #     root_url + "/" + prout + '/' + "聊天没推荐就支付了"
        # )

    _num_tokens = chat_return_tokens("gpt-3.5-turbo-0301", josnl_list)

    return _num_tokens


root_url = "C:\\Users\\F3423\\PycharmProjects\\pythonProject1\\r1_transformed_training"
# for dirpath, dirnames, filename in os.walk(root_url):
#     file_names = filename
# for file in file_names:
#     try:
#         excel_file = root_url + "/" + file
#         replace = "用户发送图片"
#         replace_1 = "推荐产品链接："
#         tojsonl(excel=excel_file,
#                 file=file,
#                 prompt="",
#                 replace_1=replace_1,
#                 file_name="wys1207_training.jsonl",
#                 root_url=root_url)

#     except Exception as e:
#         raise e
# 获取文件列表
file_names = os.listdir(root_url)
random.shuffle(file_names)  # 打乱文件列表顺序

train_count = 0
validation_count = 0

total_tokens = 0
for file in file_names:
    try:
        excel_file = os.path.join(root_url, file)
        # replace = "用户发送图片"
        replace_1 = "推荐产品链接："

        # 设置训练集和验证集的文件名
        if train_count < 1270:
            output_file = "wys0109_training.jsonl"
            train_count += 1
        else:
            output_file = "wys0109_validation.jsonl"
            validation_count += 1

        tojsonl(excel=excel_file,
                file=file,
                prompt="",
                replace_1=replace_1,
                file_name=output_file,
                root_url=root_url)

        num = tojsonl(excel=excel_file,
                      file=file,
                      prompt="",
                      replace_1=replace_1,
                      file_name=output_file,
                      root_url=root_url)
        total_tokens += num

        if train_count == 1270 and validation_count == 318:  # 8/2开
            print(f"total_tokens:{total_tokens}")
            break  # 达到目标文件数量后结束循环

    except Exception as e:
        raise e
