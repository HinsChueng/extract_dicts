import fitz

from log import get_logger
from config import ARTICLE_PATH

logger = get_logger(__name__)

file_name = '第10期 艾级计算系统若干挑战问题的思考.pdf'

doc = fitz.Document(ARTICLE_PATH + '/' + file_name)

try:

    # page = doc.pages(0, 1)
    page = doc.load_page(1)
    mat = fitz.Matrix(1, 1)  # 1.5表示放大1.5倍
    rect = page.rect
    clip = fitz.Rect(0, 0.87 * rect.height,
                     rect.width * 0.8, rect.height)
    pix = page.get_pixmap(matrix=mat, alpha=False, clip=clip)
    pix.save('test.png')

    doc = fitz.Document(ARTICLE_PATH + '/' + file_name)
except Exception as e:
    print(e)
finally:
    doc.close()
