import os
import re
import shutil
from log import get_logger

image_com = re.compile(r'图(\d{1,3}.*?)')
table_com = re.compile(r'表(\d{1,3}.*?)')

path = '/Users/joeyon/Desktop/期刊/图表提取结果/第二期'
path_problem = '/Users/joeyon/Desktop/期刊/图表提取结果/第二期/有问题的'
path_ok = '/Users/joeyon/Desktop/期刊/图表提取结果/第二期/审核过的'

logger = get_logger(__name__)

for p in [path_ok, path_problem]:
    if not os.path.exists(p):
        os.makedirs(p)


def is_ok(fn_list):
    fn_list = sorted(fn_list)

    for i, v in enumerate(fn_list):
        if i + 1 != v:
            return False

    return True


for d in os.listdir(path):
    t_list, img_list = [], []
    fp = path + '/' + d

    if not os.path.isdir(fp):
        continue

    for f in os.listdir(fp):
        info = image_com.search(f)
        if info and info[1]:
            img_list.append(int(info[1]))

        info = table_com.search(f)
        if info and info[1]:
            t_list.append(int(info[1]))

    if is_ok(img_list) and is_ok(t_list):
        shutil.move(fp, path_ok)
        logger.info('{}  --->   {}'.format(fp, path_ok))
    else:
        shutil.move(fp, path_problem)
        logger.info('{}  --->   {}'.format(fp, path_problem))
