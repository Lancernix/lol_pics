import os
import requests
from lxml import etree
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException
import time


def get_all_url(browser, nav_url):
    """
    根据导航页获取所有英雄名称和详情页url
    :param browser: webdriver对象
    :param nav_url: 导航页url
    :return: 英雄信息列表
    """
    # 使用requests无法获取英雄列表，使用selenium实现
    browser.get(nav_url)
    # 导航页源码
    nav_content = browser.page_source
    # 使用xpath解析出目标url
    nav_html = etree.HTML(nav_content)
    # 获取英雄名称列表
    name_list = nav_html.xpath('//ul[@id="jSearchHeroDiv"]/li/a/@title')
    # 获取英雄详情页部分url
    part_url_list = nav_html.xpath('//ul[@id="jSearchHeroDiv"]/li/a/@href')
    # 两项组合
    champ_info = ([name_list[i], part_url_list[i]] for i in range(len(name_list)))
    # 修改英雄详情页url
    pre_str = 'https://lol.qq.com/data/'
    for item in champ_info:
        item[1] = pre_str + item[1]
        yield item


def get_one_champion(browser, item):
    """
    获取一个英雄的所有皮肤图片信息
    :param browser: webdriver对象
    :param item: 对应英雄信息列表
    :return: 皮肤信息列表
    """
    item[0] = item[0].replace(' ', '')  # 去除空格
    # 打开新的浏览器窗口并切换
    browser.execute_script('window.open()')
    browser.switch_to.window(browser.window_handles[-1])
    browser.get(item[1])
    # explicit wait　显式等待，加载完成需要的元素之后，才进行点击操作
    try:
        wait = WebDriverWait(browser, 5)  # 最长等待时间5秒
        # xpath的下标是从１开始的，不是０
        button = wait.until(ec.element_to_be_clickable((By.XPATH, '//ul[@id="skinNAV"]/li[2]')))
    except TimeoutException:
        # 出现超时异常便刷新页面
        browser.refresh()
        # 等待1秒，防止未加载出来
        time.sleep(1)
        button = browser.find_element_by_xpath('//ul[@id="skinNAV"]/li[2]')
    finally:
        button.click()
    # xpath解析网页提取皮肤url和名称
    html = etree.HTML(browser.page_source)
    # 关闭当前窗口并切换到第一个窗口
    browser.close()
    browser.switch_to.window(browser.window_handles[-1])
    info = html.xpath('//ul[@id="skinBG"]/li/img/attribute::*')
    # 整理皮肤信息列表
    for i in range(0, len(info), 2):
        pic_list = [item[0], info[i], info[i + 1]]  # 英雄名称　皮肤url 皮肤名称
        yield pic_list


def save_pics(path, pics_list):
    """
    保存图片到文件夹中
    :param path: 文件夹路径
    :param pics_list: 图片url列表
    :return: NONE
    """
    # 英雄文件夹创建标志
    path_flag = False
    # 保存所属英雄的所有皮肤图片
    for item in pics_list:
        # 创建英雄文件夹
        if path_flag is False:
            champ_path = path + '/' + item[0]
            try:
                os.mkdir(champ_path)
                path_flag = True
            except FileExistsError:
                print('英雄文件夹已存在！')
                path_flag = True
        content = get_one_pic_content(item[1])
        # 去除名称中的/，防止路径错误
        if '/' in item[2]:
            item[2] = item[2].replace('/', '')
        # 设置路径和图片名称
        pic_path = champ_path + '/' + '%s.jpg' % item[2]
        with open(pic_path, 'wb') as f:
            f.write(content)
    return


def get_one_pic_content(pic_url):
    """
    获取一张图片的content
    :param pic_url: 图片地址
    :return: content
    """
    r = requests.get(pic_url)
    return r.content


def main():
    start_time = time.time()
    # 创建文件夹
    path = 'lol_skin_pics'
    try:
        os.mkdir(path)
    except FileExistsError:
        print('文件夹已存在，无需创建！')
    # 开启浏览器，并设置为无界面模式
    options = Options()
    options.add_argument('--headless')
    browser = webdriver.Firefox(options=options)
    nav_url = 'https://lol.qq.com/data/info-heros.shtml'
    champ_list = get_all_url(browser, nav_url)
    for item in champ_list:
        pics_list = get_one_champion(browser, item)
        save_pics(path, pics_list)
    # 关闭浏览器
    browser.quit()
    finish_time = time.time()
    total_time = finish_time - start_time
    print('所有图片已保存！乌拉～～')
    print('总用时：' + str(total_time))


if __name__ == '__main__':
    main()
