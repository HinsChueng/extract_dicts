ARTICLE_PATH = '/Users/joeyon/Desktop/期刊/原文/第二期'
RESULT_PATH = 'files/results'

# 是否保留三级标题
REMAIN_THIRD_TITLE = True

# 以下为保存图像配置
# pdf缩放倍率
ZOOM_FACTOR = 3
# 表头高度，用于屏蔽表头
HEADER_HEIGHT = 60
# 图表下标字体高度,用于搜索下标
SUBSCRIPT_HEIGHT = 22
# 不提取的表格名称列表
EXCLUDED_NAMES = ['参考文献', 'CCF', '特邀专栏作家']
# 同一页面两表的间隔
TABLE_GAP = 50
# 提取出的图表存放位置
IMAGE_SAVE_PATH = 'files/images/{}'.format(ARTICLE_PATH.split('/')[-1])

