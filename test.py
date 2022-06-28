import os
import re
import shutil

from config import ARTICLE_PATH
from filter_images import TextClassifier, TITLE_COMPILE
from log import get_logger

image_com = re.compile(r'图(\d{1,3}.*?)')
table_com = re.compile(r'表(\d{1,3}.*?)')

path = './files/images/第二期'
path_problem = '/Users/joeyon/Desktop/期刊/图表提取结果/第二期/有问题的'
path_ok = '/Users/joeyon/Desktop/期刊/图表提取结果/第二期/审核过的'
COMPILE = re.compile(r'([\u4e00-\u9fa5].*)')

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


def classify():
    for d in os.listdir(path):
        t_list, img_list = [], []
        fp = path + '/' + d

        if not os.path.isdir(fp):
            continue

        f_list = os.listdir(fp)
        # 目录为空，标记为有问题
        if not f_list:
            shutil.move(fp, path_problem)
            logger.info('{}  --->   {}'.format(fp, path_problem))
        else:
            for f in f_list:
                info = image_com.search(f)
                if info and info[1]:
                    img_list.append(int(info[1]))

                info = table_com.search(f)
                if info and info[1]:
                    t_list.append(int(info[1]))

            # 图、表序号都正确，标记为没问题
            if is_ok(img_list) and is_ok(t_list):
                shutil.move(fp, path_ok)
                logger.info('{}  --->   {}'.format(fp, path_ok))
            else:
                shutil.move(fp, path_problem)
                logger.info('{}  --->   {}'.format(fp, path_problem))


def title_from_path(path):
    ret = TITLE_COMPILE.search(path)
    if ret and ret[1]:
        return ret[1]

    return ''


def find_no_title_article():
    left_files = os.listdir(ARTICLE_PATH)

    for p in [path_ok, path_problem]:
        for handled_name in os.listdir(p):
            for i, unhandled_name in enumerate(left_files):
                if handled_name in unhandled_name:
                    left_files.pop(i)

    print(left_files)
    print(len(left_files))
    # for file_name in left_files:
    #     fpath = ARTICLE_PATH + '/' + file_name
    #     obj = TextClassifier(fpath)
    #     obj.save()


classify()
