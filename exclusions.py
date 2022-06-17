import re

EXCLUDED_WORDS = [
    '张为华',
    '邓中翰',
]

EXCLUDED_FONTS = {
    'Flama', 'FZHTK', 'FZKTJW', 'FZY3JW', 'FZBSJW', 'FZY1K', 'FZDBSJW', 'FZZDXK', 'FZSSK', 'FZXBSJW',
    'FZSSJW', 'FZDHTJW', 'FZSY', 'FZZYJW', 'FZSYK', 'FZKTK', 'FZXKJW', 'FZDHTK', 'FZHTJW', 'Footlight',
    # 'FZXBSK',
    'FZZDXJW', 'FangSong', 'FZDBSK', 'FZY1JW', 'FZSYJW', 'FZLSJW'
}

FONT_COMPILE = re.compile(r'^[a-zA-Z]{6}\+(F[a-zA-Z1-9]{3,8})-{0,2}[a-zA-Z]*')

OTHER_WORDS = [
    '参考文献',
    '致谢',
    "延伸阅读"
]


class Title:
    """文章标题"""
    size = 28
    level = 0


class PrimaryTitle:
    """一级标题"""
    size = 16
    level = 1


class SecondaryTitle:
    """二级标题"""
    size = 14
    level = 2


class ThirdLevelTitle:
    """三级标题"""
    size = 11
    level = 3
