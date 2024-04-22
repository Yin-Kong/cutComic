import os

import cv2
import numpy as np
# from epub_conversion import convert_images_to_epub, convert_epub_to_images
import ebooklib.epub as epub
import ebooklib
import re


def convert_epub_to_images(epub_path):
    epub_file = epub_path
    book = epub.read_epub(epub_file)
    cv_images = []
    cv_dict = {}
    images= book.get_items_of_type(ebooklib.ITEM_IMAGE)
    for image in images:
        img_numpy=np.frombuffer(image.content,dtype=np.uint8)
        cv_img = cv2.imdecode(img_numpy,1)
        cv_dict[image.file_name] = cv_img
        # cv_images.append(cv_img)
        # print(image)
    htmls= book.get_items_of_type(ebooklib.ITEM_DOCUMENT)
    pattern = 'src="../image/[^"]+\.(jpg|png)"'
    for html in htmls:
        html_content = html.content.decode('utf-8')
        result = re.search(pattern, html_content).group(0)[8:-1]
        if result not in cv_dict.keys():
            continue
        cv_images.append(cv_dict[result])
    return cv_images
    for item in book.items:
        if item.get_type() == epub.ITEM_IMAGE:
            image_paths.append(item.get_name())
    cv2_images = []
    for path in image_paths:
        image = cv2.imread(path)
        cv2_images.append(image)
    return cv2_images

def auto_split_comic(image):
    # 转换为灰度图像
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 进行边缘检测
    edges = cv2.Canny(gray, 100, 200)

    # 查找轮廓
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 筛选和排序轮廓
    comic_contours = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / h
        if 0.125 < aspect_ratio < 8 and w > 100 and h > 100:
            comic_contours.append((x, y, w, h))

    comic_contours.sort(key=lambda x: (int(x[1]/100), -x[0]))

    return comic_contours


def enhance_contrast(image):
    # 增强对比度
    alpha = 3
    beta = -100
    enhanced_image = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    # enhanced_image = cv2.equalizeHist(image)

    return enhanced_image


def save_comic_as_png(image, comic_contours,page,output_path):
    for i, (x, y, w, h) in enumerate(comic_contours):
        cell_image = enhance_contrast(image[y:y + h, x:x + w])
        filename = output_path+"cell_{0}_{1}.png".format(page,i)
        cv2.imwrite(filename, cell_image)


def save_comic_as_epub(image, comic_contours, output_epub,page,toc_list):
    # images = [enhance_contrast(image[y:y + h, x:x + w]) for x, y, w, h in comic_contours]
    # convert_images_to_epub(images, output_epub)
    for i, (x, y, w, h) in enumerate(comic_contours):
        cell_image = enhance_contrast(image[y:y + h, x:x + w])
        _,cell_encoded = cv2.imencode('.jpg',cell_image)
        EpubImg=epub.EpubImage(uid=f'Img {page} {i}',content=cell_encoded.tobytes(), file_name =f'image/img_{page}_{i}.jpg', media_type='image/jpeg')
        book.add_item(EpubImg)
        chapter = epub.EpubHtml(title=f'Page {page} {i}', file_name=f'html/page_{page}_{i}.xhtml')
        content = f'<html><head></head><body><img src="../{EpubImg.file_name}"/></body></html>'
        chapter.set_content(content)
        toc_list.append(chapter)
        book.add_item(chapter)


def read_jpg_image(file_path):
    image = cv2.imread(file_path)
    return image


origin_path = 'origin'
output_path = './output/'
for root, dirs, files in os.walk(origin_path):
    for file in files:
        book = epub.EpubBook()
        book.set_identifier('YKcut')
        book.set_title(file)
        book.set_language('en')
        book.add_author('YK')
        page = 0
        toc_list = []
        images = convert_epub_to_images(os.path.join(root, file))
        for image in images[5:]:
            page+=1
            contours=auto_split_comic(image)
            # save_comic_as_png(image,contours,page,'./tmp/')
            save_comic_as_epub(image,contours,book,page,toc_list)
        # 定义CSS样式
        style = 'body { margin: 0; padding: 0; } img { margin: 0; padding: 0; }'
        nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
        book.add_item(nav_css)
        book.toc = tuple(toc_list)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        spine = ['nav']
        spine.extend(toc_list)
        book.spine=spine
        epub.write_epub(output_path+file,book)



