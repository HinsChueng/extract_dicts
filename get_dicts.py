import os
import traceback
from typing import List, Dict

import pdfplumber

from config import RESULT_PATH, ARTICLE_PATH
from exclusions import Title, PrimaryTitle, SecondaryTitle, ThirdLevelTitle
from log import get_logger
from tree import Tree, Node

if not os.path.exists(RESULT_PATH):
    os.makedirs(RESULT_PATH)

__KEYS__ = [
    'matrix',  # 此字符的“当前转换矩阵”。
    'fontname',  # 字符的字体。
    'adv',  # 等于文本宽度字体大小缩放因子。
    'upright',  # 字符是否是直立的。
    'x0',  # 字符左侧到页面左侧的距离
    'y0',  # 字符底部到页面底部的距离。
    'x1',  # 字符右侧到页面左侧的距离。
    'y1',  # 字符顶部到页面底部的距离
    'width',  # 字符宽度。
    'height',  # 字符高度。
    'size',  # 字号。
    'object_type',  # "char"或"anno"
    'page_number',  # 找到此字符的页码。
    'text',  # 字符文本，如"z"、“Z"或者"你”。
    'stroking_color',  # 字符轮廓的颜色（即笔触），表示为元组或整数，具体取决于使用的“颜色空间”。
    'non_stroking_color',  # 角色的内部颜色。
    'top',  # 字符顶部到页面顶部的距离。
    'bottom',  # 字符底部到页面顶部的距离。
    'doctop',  # 字符顶部到文档顶部的距离。
]

log = get_logger()


class TextClassifier(object):
    def __init__(self, pdf_path):
        # pdf对象
        self.pdf = pdfplumber.open(pdf_path)
        # 存放目录的树
        self.tree = Tree(Node())
        self.pre_node = None
        self.last_count = -1

    @staticmethod
    def iter_successive_text(chars: List[Dict]) -> str:
        """
        获取连续的、同一类型的（即同一层级的）信息。

        :param chars: pdf中获取的元素信息列表
        :return:
        """
        i, j = 0, 0
        length = len(chars)

        while j < length:
            if chars[i]['size'] == chars[j]['size']:
                j += 1
                if j == length:
                    yield chars[i:j]

            else:
                if j - i > 1:
                    yield chars[i:j]

                i = j

    def set_title(self, count, **kwargs):
        if self.pre_node is None:
            self.tree.update(self.tree.root, **kwargs)
        else:
            pre_size, size = getattr(self.pre_node, 'size'), kwargs['size']

            if pre_size == size:
                kwargs['text'] = ''.join([
                    getattr(self.pre_node, 'text'),
                    kwargs['text']
                ])

            self.tree.update(self.tree.root, **kwargs)

        self.pre_node = self.tree.root

    def level_correct(self, count, **kwargs):
        pre_size, size = getattr(self.pre_node, 'size'), kwargs['size']

        if pre_size == size:
            if count == self.last_count + 1:
                kwargs['text'] = ''.join([getattr(self.pre_node, 'text'), kwargs['text']])
                self.tree.update(self.pre_node, **kwargs)
            else:
                _, pre_parent_node = self.tree.find_parent_node(self.pre_node)
                node = Node(**kwargs)
                self.tree.insert(pre_parent_node, node)
                self.pre_node = node

        elif pre_size > size:
            node = Node(**kwargs)
            self.tree.insert(self.pre_node, node)
            self.pre_node = node

        else:
            _, pre_parent_node = self.tree.find_parent_node(self.pre_node)
            if not getattr(pre_parent_node, 'text', ''):
                self.tree.update(pre_parent_node, **kwargs)
                self.pre_node = pre_parent_node
            else:
                node = Node(**kwargs)
                _, pre_2_parent_node = self.tree.find_parent_node(pre_parent_node)
                self.tree.insert(pre_2_parent_node, node)
                self.pre_node = node

    def set_pri_title(self, count, **kwargs):
        if not self.pre_node:
            node = Node(**kwargs)
            self.tree.insert(self.tree.root, node)
            self.pre_node = node
        else:
            self.level_correct(count, **kwargs)

    def set_sec_title(self, count, **kwargs):
        if not self.pre_node:
            pri_node, sec_node = Node(), Node(**kwargs)
            self.tree.insert(self.tree.root, pri_node)
            self.tree.insert(pri_node, sec_node)
            self.pre_node = sec_node
        else:
            self.level_correct(count, **kwargs)

    def set_third_level_title(self, count, **kwargs):
        if not self.pre_node:
            pri_node, sec_node, thd_node = Node(), Node(), Node(**kwargs)
            self.tree.insert(self.tree.root, pri_node)
            self.tree.insert(pri_node, sec_node)
            self.tree.insert(sec_node, thd_node)
            self.pre_node = thd_node
        else:
            self.level_correct(count, **kwargs)

    def handle_text(self, count: int, chars: List[Dict]):
        size = int(round(chars[0]['size']))

        params = dict()
        params.update(chars[0])
        params['fontname'] = chars[0]['fontname'],
        params['text'] = ''.join([item['text'] for item in chars])
        params['size'] = size

        # 屏蔽页眉
        if params['bottom'] <= 55:
            return

        if size >= Title.size:
            self.set_title(count, **params)
            self.last_count = count

        elif size == PrimaryTitle.size:
            self.set_pri_title(count, **params)
            self.last_count = count

        elif size == SecondaryTitle.size:
            self.set_sec_title(count, **params)
            self.last_count = count

        elif size == ThirdLevelTitle.size:
            self.set_third_level_title(count, **params)
            self.last_count = count

    def classify(self):
        """
        分类，并将结果添加到`self.result`中

        :return:
        """
        try:
            for page in self.pdf.pages:
                for count, attr_list in enumerate(self.iter_successive_text(page.chars)):
                    self.handle_text(count, attr_list)
                    size = attr_list[0]['size']
                    bottom = attr_list[0]['bottom']
                    if size >= ThirdLevelTitle.size and bottom > 55:
                        print(str(int(round(size))) + ' - ' + ''.join([i['text'] for i in attr_list]))
        except Exception as e:
            log.error(traceback.format_exc())
        finally:
            self.pdf.close()


def test():
    # file_name = '第3期 交互式搜索意图理解：超越传统搜索的信息发现.pdf'
    # file_name = '第12期 移动互联网时代的位置服务.pdf'
    file_name = '第10期 艾级计算系统若干挑战问题的思考.pdf'
    # file_name = '第10期 百毒不侵的电脑是怎样练成的.pdf'
    obj = TextClassifier(ARTICLE_PATH + '/' + file_name)
    obj.classify()
    # print(obj.tree.pre_order())
    print(obj.tree.to_dict())


if __name__ == '__main__':
    path = ARTICLE_PATH
    # path = 'files/test_pdfs'
    # run(path)
    test()
