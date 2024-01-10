import pandas as pd
import os

# 定义文件夹路径
source_folder = './r1_transformed'
target_folder = './r1_transformed_training'
target_folder1 = './r1_transformed_pending'

if not os.path.exists(target_folder):
    os.makedirs(target_folder)
if not os.path.exists(target_folder1):
    os.makedirs(target_folder1)
# 遍历文件夹中的所有文件
for filename in os.listdir(source_folder):
    # 检查文件扩展名是否为 .xlsx
    if filename.endswith('.xlsx'):
        # 构造完整的文件路径
        file_path = os.path.join(source_folder, filename)

        # 读取 Excel 文件
        df = pd.read_excel(file_path)

        # 强制将 content 列转换为字符串类型
        df['content'] = df['content'].astype(str)

        # 将整个create_time列的值统一
        # first_value = df.at[0, 'created_time']
        # df['created_time'] = first_value

        # 在这里进行数据清洗操作
        # 查找包含特定文本的行
        target_text = "粉丝成功支付订单"
        row_to_keep = -1

        # 逐行检查是否包含目标文本
        for index, row in df.iterrows():
            if target_text in str(row['content']):
                row_to_keep = index
                break

        # 检查是否找到了目标行
        if row_to_keep != -1:
            # 保留找到的行及之前的所有行
            df = df.iloc[:row_to_keep + 1]

        df.at[0, 'content'] = "系统提示：用户点击了菜单：我要找小希"  # 统一第一句话
        df['content'] = df['content'].str.replace('/::', '', regex=True)  # 删除表情包
        df['content'] = df['content'].str.replace('那就没问题了，', '')
        df['content'] = df['content'].str.replace('昨天', '')  # 删除时间相关
        df['content'] = df['content'].str.replace('【收到不支持的消息类型，暂无法显示】', '')  # 删除不支持的消息类型
        df['content'] = df['content'].str.replace('➕', '+')  # 修改特殊符号
        df['content'] = df['content'].str.replace('稍等2分钟', '稍等俩分钟')  # 标准化数据
        # 筛选出 send 列为 'customer' 的行
        filtered_rows = df[df['send'] == 'customer']

        # 选择 send 列为 'customer' 且 content 列包含 '哪个快递' 的行，然后替换 content 列
        df.loc[
            (df['send'] == 'customer') & (df['content'].str.contains('哪个快递', na=False)), 'content'] = \
            "老师这边可以发送申通、顺丰，都是包邮的，你看哪个快递方便签收呢？"

        # 找出 send 列为 customer 且 content 列包含 "稍等一下" 的行的索引
        target_indices = df[(df['send'] == 'customer') &
                            (df['content'].str.contains(
                                '稍等一下|设置好了|稍等俩分钟|稍等|痘痘痘印还是一直反复|收到我的消息|你先设置一下呢|长期使用'))].index  # 新增“痘痘痘印还是一直反复”，“长期使用”

        # 对每个目标索引进行处理
        for index in target_indices:
            # 找到下一个 send 列为 customer 的索引
            next_customer_index = df[(df['send'] == 'customer') & (df.index > index)].index.min()

            # 如果找到了下一个 customer 行，删除中间的 user 行
            if pd.notna(next_customer_index):
                df.drop(df[(df['send'] == 'user') & (df.index > index) & (df.index < next_customer_index)].index,
                        inplace=True)

        # 对 content 列应用自定义的条件删除函数
        def conditional_remove(row):
            words_to_remove = ['好的，', '嗯嗯，', '好呢，', 'OK，', '好的。', '嗯嗯。', '好呢。', 'OK。', '好的', '嗯嗯',
                               '好呢', 'OK', '好吧', '好吧，', '好吧。', '嗯', '嗯，', '嗯。', '好', '好，', '好了。',
                               '好了，',
                               'ok', '好了。', 'Ok',
                               '好。']  # 加入 '好吧'
            if row['send'] == 'user':
                modified_content = str(row['content'])
                for word in words_to_remove:
                    modified_content = modified_content.replace(word, '').strip()
                # 如果修改后的内容为空，则返回 NaN（之后将被删除）
                return modified_content if modified_content else pd.NA
            return row['content']  # 对于非'user'的行保持原样


        df['content'] = df.apply(conditional_remove, axis=1)

        #  删除粉丝成功支付订单之后的所有行
        # count = (df['content'] == '粉丝成功支付订单').sum()
        #
        # if count == 2:  # 如果出现两次，存入pending文件夹
        #     target_file_path1 = os.path.join(target_folder1, filename)
        #     df.to_excel(target_file_path1, index=False)
        # elif count == 1:
        #     idx = df[df['content'] == '粉丝成功支付订单'].index[0]
        #     df = df[:idx + 1]

        # 删除 content 列为空的行
        df.dropna(subset=['content'], inplace=True)

        # 确保 created_time 列是日期时间格式
        df['created_time'] = pd.to_datetime(df['created_time'], format='%Y-%m-%d %H:%M:%S')

        # 检查是否转到微信成交
        # condition_met = False
        # payment_index = df[df['content'].str.contains('系统提示:粉丝成功支付订单')].index
        # wechat_index = df[df['content'].str.contains('微信')].index
        #
        # for payment_i in payment_index:
        #     for wechat_i in wechat_index:
        #         if payment_i > wechat_i:
        #             condition_met = True
        #             break
        #     if condition_met:
        #         break

        # 如果条件满足，保存文件到pending文件夹，否则保存到target_folder
        # if condition_met:
        #     target_file_path = os.path.join(target_folder1, filename)
        # else:  # 检查“粉丝成功支付订单”出现的次数
        #     count = (df['content'] == '粉丝成功支付订单').sum()
        #
        #     if count >= 2:
        #         # 找到第二次出现的索引
        #         idx_list = df[df['content'] == '粉丝成功支付订单'].index
        #         second_occurrence_idx = idx_list[1]
        #
        #         # 删除第二次出现及之后的所有行
        #         df = df[:second_occurrence_idx]

        # target_file_path = os.path.join(target_folder, filename)
        #
        # # 存储文件
        # df.to_excel(target_file_path, index=False)

        # 检查是否存在跨天情况
        if df['created_time'].dt.date.nunique() > 1:
            # 构造目标文件路径
            target_file_path1 = os.path.join(target_folder1, filename)

            # 保存文件到目标文件夹
            df.to_excel(target_file_path1, index=False)

        # if not df['content'].str.contains('今年多大了').any():
        #     # 保存清洗后的数据到新的 Excel 文件
        #     target_file_path1 = os.path.join(target_folder1, filename)
        #
        #     # 保存文件到目标文件夹
        #     df.to_excel(target_file_path1, index=False)
        else:
            # 保存清洗后的数据到新的 Excel 文件
            target_file_path = os.path.join(target_folder, filename)
            df.to_excel(target_file_path, index=False)

        # 筛选出有问年龄的数据集
        # if df['content'].str.contains('今年多大了').index:
        #     target_file_path = os.path.join(target_folder,filename)
        #     df.to_excel(target_file_path,index=False)
        # else:
        #     target_file_path1=os.path.join(target_folder1,filename)
        #     df.to_excel(target_file_path1,index=False)

        # 输出清洗后的数据预览
        print(f"Cleaned Data from {filename}:")

print('Data Cleansing Finished Successfully')
