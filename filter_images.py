import functools
import os
import re
import traceback
from typing import List, Tuple, Dict

import fitz
import pdfplumber

from config import (
    ZOOM_FACTOR,
    IMAGE_SAVE_PATH,
    ARTICLE_PATH,
    HEADER_HEIGHT,
    SUBSCRIPT_HEIGHT,
    EXCLUDED_NAMES
)
from pdfplumber.page import Page
from exclusions import Title
from log import get_logger
from itertools import groupby

if not os.path.exists(IMAGE_SAVE_PATH):
    os.makedirs(IMAGE_SAVE_PATH)

logger = get_logger('get_images')
error_logger = get_logger('get_images_error')

SUBSCRIPT_COMPILE = re.compile(r'([图表]\d{1,3}.*)')
PAGE_NO_COMPILE = re.compile(r'^(\d*)$')
REFERENCE_COMPILE = re.compile(r'(\[\d.*][\u4e00-\u9fa5a-zA-Z]+)')
BLANK_COMPILE = re.compile(r'\s+')
TITLE_COMPILE = re.compile(r'(第\d+期\s.*?.*?)\.pdf')

Coordinates = Tuple[float, float, float, float]


def after_save(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AssertionError:
            error_logger.error('pdf读取失败： {}'.format(args[0].pdf_path))
        except Exception as e:
            error_logger.error('pdf解析出错： %s', args[0].pdf_path)
            error_logger.error(str(e))
            error_logger.error(traceback.format_exc())
        finally:
            self = args[0]
            self.text_doc.close()
            self.image_doc.close()
            logger.info('{} 完成！\n'.format(self.pdf_path))

    return inner


def _int(v):
    return int(v // 10 * 10)


class TextClassifier(object):
    def __init__(self, pdf_path):
        # 用于解析文本、图表坐标的pdf对象, 页码从1开始
        self.text_doc = pdfplumber.open(pdf_path)
        # 用于截图的pdf对象，页码从0开始
        self.image_doc = fitz.Document(pdf_path)
        self.pdf_path = pdf_path
        self.cur_page_img_dict = dict()
        self.cur_page_img_no = 0

        path = os.path.join(IMAGE_SAVE_PATH, self.title)
        if not os.path.exists(path):
            os.makedirs(path)

        self.save_path = path

    @property
    def text_pages(self):
        return self.text_doc.pages

    @property
    def title_from_path(self):
        res = TITLE_COMPILE.search(self.pdf_path)
        if res and res[1]:
            return res[1]

        return self.pdf_path.split('/')[-1].strip('.pdf')

    @property
    def title(self) -> str:
        """
        获取文章标题
        :return:
        """
        title = self.title_from_path
        tmp_title = ''
        pages = self.text_pages
        if not pages:
            return title

        try:
            for c in pages[0].chars:
                if c['text'].startswith('(cid'):
                    return '水印-{}'.format(title)
                if c['size'] >= Title.size:
                    tmp_title += c['text']
        finally:
            return title if title else tmp_title

    @staticmethod
    def is_header(y1):
        """是否为页眉"""
        return True if y1 <= HEADER_HEIGHT else False

    @staticmethod
    def is_footer(h, y0):
        return True if h - y0 <= HEADER_HEIGHT else False

    @staticmethod
    def is_references(text) -> bool:
        """是否为参考文献 """
        if '参考文献' in text:
            return True

        text = re.sub(BLANK_COMPILE, '', text)
        ref_info = REFERENCE_COMPILE.search(text)

        return True if ref_info else False

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
            s1, s2 = int(round(chars[i]['size'])), int(round(chars[j]['size']))
            if s1 == s2:
                j += 1
                if j == length:
                    yield ''.join([c['text'] for c in chars[i:j]])

            else:
                if j - i > 1:
                    yield ''.join([c['text'] for c in chars[i:j]])

                i = j

    def crop(self, page_no, cds):
        page = self.text_pages[page_no]
        x0, y0, x1, y1 = cds

        x0 = x0 if x0 > 0 else 0
        y0 = y0 if y0 > 0 else 0
        x1 = x1 if x1 < page.width else page.width
        y1 = y1 if y1 < page.height else page.height

        return page.crop([x0, y0, x1, y1])

    def get_subscript(self, page_no, coordinates: Coordinates):
        """
        获取图表下标名称
        :param page_no: 当前页码，0为起始页
        :param coordinates: 在以矩形左上角为原点，x轴水平向右，y轴垂直向下的坐标系中，
                           （x0,y0)---左上角的坐标，(x1,y1)---右下角的坐标
        :return:
        """

        def get_name_in_box(cds):
            ret = []

            chars = self.get_text_in_box(page_no, cds)
            for s in self.iter_successive_text(chars):
                m = SUBSCRIPT_COMPILE.search(s)
                if not m:
                    continue

                _name = m[1][:100].replace('/', '_')
                ret.append(_name)

            return ret

        page_obj = self.text_pages[page_no]
        x0, y0, x1, y1 = coordinates
        c1 = (x0 - 5, y0 - SUBSCRIPT_HEIGHT, x1 + 5, y0)
        c2 = (x0 - 5, y1, x1 + 5, y1 + SUBSCRIPT_HEIGHT)

        c1_names, c2_names = get_name_in_box(c1), get_name_in_box(c2)
        if not c1_names and not c2_names:
            return ''

        if c2_names:
            name = c2_names[-1]
        else:
            name = c1_names[-1]

        return name

    def get_text_in_box(self, page_no, coordinates: Coordinates):
        """
        在坐标对确定的矩形中，提取文本
        :param page_no: pdf页码，从0开始
        :param coordinates: 坐标对
        :return:
        """
        page = self.text_pages[page_no]
        x0, y0, x1, y1 = coordinates

        if x0 == x1 or y0 == y1:
            return ''

        x0 = x0 if x0 > 0 else 0
        y0 = y0 if y0 > 0 else 0
        x1 = x1 if x1 < page.width else page.width
        y1 = y1 if y1 < page.height else page.height

        return page.crop([x0, y0, x1, y1]).chars

    def get_area(self, cds):
        return (cds[2] - cds[0]) * (cds[3] - cds[1])

    def save_page_objects(self, page, coordinates_list: List[Coordinates]):
        """
        根据坐标保存每页的所有对象

        :param page: 表示文档页的类。页面对象由fitz.Document.load_page()创建，或者等效地通过索引文档创建
        :param coordinates_list:
        :return:
        """
        mat = fitz.Matrix(ZOOM_FACTOR, ZOOM_FACTOR)

        for c in coordinates_list:
            # 提取图片下标，如果获取不到用页码+数字取名
            pic_name = self.get_subscript(page.number, c)

            if pic_name in self.cur_page_img_dict:
                if self.get_area(c) < self.get_area(self.cur_page_img_dict[pic_name]):
                    continue

            if not pic_name:
                pic_name = 'page_{}_{}'.format(page.number, self.cur_page_img_no)

            clip = fitz.Rect(*c)
            pix = page.get_pixmap(matrix=mat, alpha=False, clip=clip)

            try:
                pix.save('{}/{}.png'.format(self.save_path, pic_name))
                self.cur_page_img_dict[pic_name] = c
                self.cur_page_img_no += 1
            except RuntimeError:
                error_logger.error('{}: {} 错误, 保存对象失败！'.format(self.pdf_path, c))
                continue

            logger.info('%s --- 保存成功！' % pic_name)

    @staticmethod
    def merge_box(c1, c2):
        x0, y0 = min(c1[0], c2[0]), min(c1[1], c2[1])
        x1, y1 = max(c1[2], c2[2]), max(c1[3], c2[3])
        return x0, y0, x1, y1

    def merge_boxs(self, page_no, boxs: List[Coordinates], direction: str):
        if not boxs:
            return ()

        if direction.lower() == 'x':
            p1, p2 = 0, 2
        elif direction.lower() == 'y':
            p1, p2 = 1, 3
        else:
            raise Exception()

        sorted_boxs = sorted(boxs, key=lambda c: (c[p1], c[p2]))
        box_list = [[int(round(v)) for v in c] for c in sorted_boxs]

        box_groups = groupby(box_list, key=lambda c: (c[p1], c[p2]))

        ret = list()
        for _, _boxs in box_groups:
            _boxs = list(_boxs)
            coordinates = _boxs[0]
            for cds in _boxs[1:]:
                tmp = self.merge_box(coordinates, cds)
                if not self.subscipt_in_box(page_no, tmp):
                    coordinates = tmp
                else:
                    ret.append(cds)
                    coordinates = cds

            ret.append(coordinates)

        return ret

    def subscipt_in_box(self, page_no, box):
        box = list(box)
        box[0] -= 5
        box[2] += 5
        sub_info = ''.join([c['text'] for c in self.get_text_in_box(page_no, box)])
        match_info = SUBSCRIPT_COMPILE.search(sub_info)
        if match_info and match_info[1]:
            return True
        return False

    def get_the_same_objects(self, page_no, tables: List[Coordinates]):
        """
        获取连续的table

        :param page_no: 页码，从0开始
        :param tables: pdf中获取的元素信息列表
        :return:
        """
        if not tables:
            return []

        length = len(tables)
        if length == 1:
            return tables

        res = self.merge_boxs(page_no, tables, 'x')
        res = self.merge_boxs(page_no, res, 'y')
        return res

    @staticmethod
    def in_or_cross_box(c1: Coordinates, c2: Coordinates):
        """
        判断两个用对角线坐标表示的矩形是否有交叉
        :param c1:
        :param c2:
        :return:
        """
        x10, y10, x11, y11 = c1
        x20, y20, x21, y21 = c2

        min_x, min_y = max(x10, x20), max(y10, y20)
        max_x, max_y = min(x11, x21), min(y11, y21)

        if min_x > max_x or min_y > max_y:
            return False
        else:
            return True

    def de_duplication(self):
        """
        删除重复的图片，如果两张图片有交叉，删除面积小的，保留面积大的
        :return:
        """
        img_list = sorted(
            self.cur_page_img_dict.items(),
            key=lambda c: (c[1][2] - c[1][0]) * (c[1][3] - c[1][1])
        )

        count = len(img_list)

        for i in range(count - 1):
            for j in range(i + 1, count):
                if self.in_or_cross_box(img_list[i][1], img_list[j][1]):
                    name = img_list[i][0]
                    fpath = '/'.join([self.save_path, name + '.png'])
                    if not os.path.exists(fpath):
                        continue

                    self.cur_page_img_dict.pop(name)
                    os.remove(fpath)
                    logger.info('删除 {}'.format(fpath))

        self.cur_page_img_dict = {}
        self.cur_page_img_no = 0

    @staticmethod
    def has_negative_coordinates(coordinates: Coordinates):
        """
        坐标对中是否包含负数
        :param coordinates: 坐标对
        :return:
        """
        cds = list(filter(lambda x: x >= 0, coordinates))
        if len(cds) < 4:
            return True

        if _int(cds[0]) == _int(cds[2]) or _int(cds[1]) == _int(cds[3]):
            return True

        return False

    def in_keywords(self, text):
        for k in EXCLUDED_NAMES:
            if k in text:
                return True

        return False

    def filter(self, text_page: Page, coordinates_list: List[Coordinates]):
        """
        过滤不合法的坐标：1、包含负数 2、页眉 3、页码（页脚）
        :param text_page: pdf页码，从0开始
        :param coordinates_list: 坐标列表
        :return: 合法的坐标列表
        """
        ret = list()

        for c in coordinates_list:

            # 屏蔽包含负数的坐标
            if self.has_negative_coordinates(c):
                continue

            # 屏蔽页眉
            if self.is_header(c[3]):
                continue

            # 屏蔽页脚
            if self.is_footer(text_page.height, c[1]):
                continue

            chars = self.get_text_in_box(text_page.page_number - 1, c)
            text = ''.join([c['text'] for c in chars])
            if self.in_keywords(text):
                continue

            # 屏蔽参考文献
            if self.is_references(text):
                continue

            ret.append(c)

        return ret

    def save_by_cds(self, text_page, image_page, obj_cds):
        obj_cds = self.filter(text_page, obj_cds)
        box_list = self.get_the_same_objects(image_page.number, obj_cds)
        self.save_page_objects(image_page, box_list)

    @after_save
    def save(self):
        for text_page in self.text_pages:
            # 用以截图的pdf页对象
            page_no = text_page.page_number - 1
            image_page = self.image_doc.load_page(page_no)

            # 保存矩形
            for items in [text_page.images, text_page.rects]:
                obj_cds = [(img['x0'], img['top'], img['x1'], img['bottom']) for img in items]
                self.save_by_cds(text_page, image_page, obj_cds)

            obj_cds = [img.bbox for img in text_page.find_tables()]
            self.save_by_cds(text_page, image_page, obj_cds)

            # 在本页中去重
            self.de_duplication()


def test():
    file_name = '第3期 交互式搜索意图理解：超越传统搜索的信息发现.pdf'
    # file_name = '第12期 移动互联网时代的位置服务.pdf'
    file_name = '第2期 弥合学术界和工业界之间的鸿沟.pdf'
    file_name = '第10期 百毒不侵的电脑是怎样练成的.pdf'
    file_name = '第1期 努力践行“重点跨越”的战略取向.pdf'
    file_name = '1607960556531098592.pdf'
    file_name = '第6期 存储虚拟化研究综述.pdf'
    file_name = '第6期 移动时代的用户态隐私.pdf'
    file_name = '第3期 互联网安全的忠诚卫士.pdf'
    file_name = '第9期 面向哈希计算的新型数据组织结构.pdf'
    file_name = '第7期 CPS行为建模及其仿真验证.pdf'
    file_name = '第2期 片上系统芯片的软硬件协同设计.pdf'
    file_name = '第1期 机器智能需要神经科学.pdf'
    file_name = '第12期 CCF@U_CCF走进高校(2017年11月).pdf'
    file_name = '第12期 2017年目录.pdf'
    file_name = '第5期 CCF代表团访问法德.pdf'
    file_name = '第12期 做顶天立地的研究培养独立的学术风格——访“2017CCF王选奖”获得者鲍虎军教授.pdf'
    file_name = '第1期 提高健康、安全和生活质量的模式识别.pdf'
    file_name = '第10期 云计算与虚拟化.pdf'
    fpath = ARTICLE_PATH + '/' + file_name
    obj = TextClassifier(fpath)
    obj.save()


def run():
    res = dict()
    for file_name in os.listdir(ARTICLE_PATH):
        if not file_name.endswith('.pdf'):
            continue

        fpath = ARTICLE_PATH + '/' + file_name
        obj = TextClassifier(fpath)
        obj.save()


if __name__ == '__main__':
    # test()
    run()
